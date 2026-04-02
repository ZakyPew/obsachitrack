"""
Avatar Router - Handles burst mode triggers and WebSocket connections
"""
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
import json
import logging

from database import SessionLocal, BurstEvent, User
from services.avatar_queue import avatar_queue, Priority, EventType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/avatar", tags=["avatar"])
security = HTTPBearer()

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time avatar updates"""
    
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}  # user_id -> websocket
        
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user {user_id}")
        
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")
            
    async def send_to_user(self, user_id: int, message: Dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                
    async def broadcast(self, message: Dict):
        """Broadcast to all connected clients"""
        disconnected = []
        for user_id, ws in self.active_connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(user_id)
        
        # Clean up disconnected clients
        for user_id in disconnected:
            self.disconnect(user_id)


ws_manager = ConnectionManager()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_from_api_key(api_key: str, db: Session) -> Optional[User]:
    """Validate API key and return user"""
    from database import ApiKey
    
    key_record = db.query(ApiKey).filter(
        ApiKey.key == api_key,
        ApiKey.is_active == True
    ).first()
    
    if key_record:
        # Update last_used
        from datetime import datetime
        key_record.last_used = datetime.utcnow()
        db.commit()
        return key_record.user
    return None


async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """Dependency to validate Bearer token and return user"""
    token = credentials.credentials
    user = get_user_from_api_key(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Pydantic models
class EventTypeEnum(str, Enum):
    ACHIEVEMENT = "achievement"
    DEATH = "death"
    KILLSTREAK = "killstreak"
    EXPLOSION = "explosion"


class BurstTriggerRequest(BaseModel):
    event_type: EventTypeEnum = Field(..., description="Type of audio event detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    game_context: Optional[str] = Field(None, description="Optional game/app context")


class BurstTriggerResponse(BaseModel):
    success: bool
    message: str
    event_id: Optional[int] = None
    cooldown_remaining: Optional[float] = None


class QueueStatusResponse(BaseModel):
    queue_size: int
    is_processing: bool
    current_item: Optional[Dict[str, Any]]
    burst_rate_limit: Dict[str, Any]


# WebSocket handler for avatar real-time updates
@router.websocket("/ws")
async def avatar_websocket(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time avatar updates.
    
    Connect with: ws://host/avatar/ws?token=YOUR_API_KEY
    
    Events sent to client:
    - burst_trigger: Burst event queued
    - burst_processing: Burst event being processed
    - burst_complete: Burst event finished
    - queue_added: Normal item added to queue
    - processing: Normal item being processed
    - complete: Normal item finished
    """
    db = SessionLocal()
    try:
        # Validate token
        user = get_user_from_api_key(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid API key")
            return
        
        await ws_manager.connect(websocket, user.id)
        
        # Send initial connection success
        await websocket.send_json({
            "type": "connected",
            "user_id": user.id,
            "username": user.username
        })
        
        # Keep connection alive and handle client messages
        try:
            while True:
                # Wait for messages from client (ping/acknowledgments)
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif msg.get("type") == "get_status":
                        status = avatar_queue.get_queue_status(user.id)
                        await websocket.send_json({"type": "status", "data": status})
                except json.JSONDecodeError:
                    pass
                    
        except WebSocketDisconnect:
            pass
        finally:
            ws_manager.disconnect(user.id)
            
    finally:
        db.close()


# HTTP endpoints
@router.post("/burst-trigger", response_model=BurstTriggerResponse)
async def burst_trigger(
    request: BurstTriggerRequest,
    user: User = Depends(validate_token),
    db: Session = Depends(get_db)
):
    """
    Trigger an immediate avatar response for a detected audio event.
    
    This endpoint bypasses the normal queue and processes immediately (burst mode).
    Rate limited: max 1 burst per 5 seconds per user.
    
    Requires: Bearer token authentication
    """
    # Log the burst event to database
    burst_event = BurstEvent(
        user_id=user.id,
        event_type=request.event_type.value,
        confidence=request.confidence,
        timestamp=request.timestamp,
        game_context=request.game_context,
        processed=False
    )
    db.add(burst_event)
    db.commit()
    db.refresh(burst_event)
    
    # Prepare payload for queue
    payload = {
        "event_id": burst_event.id,
        "confidence": request.confidence,
        "game_context": request.game_context
    }
    
    # Add to avatar queue with burst priority
    success, message = await avatar_queue.enqueue(
        user_id=user.id,
        event_type=request.event_type.value,
        priority=Priority.BURST,
        payload=payload,
        timestamp=request.timestamp
    )
    
    if not success:
        # Rate limited
        cooldown = avatar_queue.get_burst_cooldown_remaining(user.id)
        return BurstTriggerResponse(
            success=False,
            message=message,
            event_id=burst_event.id,
            cooldown_remaining=cooldown
        )
    
    return BurstTriggerResponse(
        success=True,
        message=message,
        event_id=burst_event.id
    )


@router.get("/queue-status", response_model=QueueStatusResponse)
async def queue_status(
    user: User = Depends(validate_token)
):
    """Get current avatar queue status for the authenticated user"""
    status = avatar_queue.get_queue_status(user.id)
    return QueueStatusResponse(**status)


@router.get("/burst-history")
async def get_burst_history(
    limit: int = 50,
    user: User = Depends(validate_token),
    db: Session = Depends(get_db)
):
    """Get burst event history for the authenticated user"""
    events = db.query(BurstEvent).filter(
        BurstEvent.user_id == user.id
    ).order_by(
        BurstEvent.created_at.desc()
    ).limit(limit).all()
    
    return {
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "confidence": e.confidence,
                "timestamp": e.timestamp,
                "game_context": e.game_context,
                "processed": e.processed,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in events
        ],
        "count": len(events)
    }


# WebSocket notification bridge
async def ws_notification_bridge(event_type: str, data: Dict):
    """Bridge avatar queue notifications to WebSocket clients"""
    user_id = data.get("user_id")
    if user_id:
        await ws_manager.send_to_user(user_id, {
            "type": event_type,
            "data": data
        })


# Register the WebSocket bridge with the avatar queue
avatar_queue.register_ws_callback(ws_notification_bridge)
