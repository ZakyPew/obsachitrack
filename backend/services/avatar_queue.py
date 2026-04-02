"""
Avatar Queue Service - Manages avatar response triggers with burst mode support
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Priority(Enum):
    NORMAL = "normal"
    BURST = "burst"

class EventType(Enum):
    ACHIEVEMENT = "achievement"
    DEATH = "death"
    KILLSTREAK = "killstreak"
    EXPLOSION = "explosion"

class AvatarQueueItem:
    """Represents an item in the avatar queue"""
    def __init__(
        self,
        user_id: int,
        event_type: str,
        priority: Priority = Priority.NORMAL,
        payload: Optional[Dict] = None,
        timestamp: Optional[int] = None
    ):
        self.user_id = user_id
        self.event_type = event_type
        self.priority = priority
        self.payload = payload or {}
        self.timestamp = timestamp or int(time.time() * 1000)
        self.created_at = datetime.utcnow()
        self.id = f"{user_id}_{self.timestamp}"

class AvatarQueue:
    """
    Priority queue for avatar triggers with burst mode support.
    
    Features:
    - Priority queue: burst events skip to front
    - Rate limiting: max 1 burst per 5 seconds per user
    - WebSocket notification support
    """
    
    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._burst_timestamps: Dict[int, float] = {}  # user_id -> last burst timestamp
        self._burst_rate_limit_seconds = 5.0
        self._lock = asyncio.Lock()
        self._ws_callbacks: List[Callable] = []
        self._processing = False
        self._current_item: Optional[AvatarQueueItem] = None
        
    def register_ws_callback(self, callback: Callable):
        """Register a WebSocket callback for real-time updates"""
        self._ws_callbacks.append(callback)
        
    def unregister_ws_callback(self, callback: Callable):
        """Unregister a WebSocket callback"""
        if callback in self._ws_callbacks:
            self._ws_callbacks.remove(callback)
    
    async def _notify_ws(self, event_type: str, data: Dict):
        """Notify all registered WebSocket callbacks"""
        for callback in self._ws_callbacks:
            try:
                await callback(event_type, data)
            except Exception as e:
                logger.error(f"WebSocket notification failed: {e}")
    
    def can_burst(self, user_id: int) -> bool:
        """Check if user can trigger a burst event (rate limiting)"""
        last_burst = self._burst_timestamps.get(user_id)
        if last_burst is None:
            return True
        elapsed = time.time() - last_burst
        return elapsed >= self._burst_rate_limit_seconds
    
    def get_burst_cooldown_remaining(self, user_id: int) -> float:
        """Get remaining cooldown time for burst events"""
        last_burst = self._burst_timestamps.get(user_id)
        if last_burst is None:
            return 0.0
        elapsed = time.time() - last_burst
        remaining = self._burst_rate_limit_seconds - elapsed
        return max(0.0, remaining)
    
    async def enqueue(
        self,
        user_id: int,
        event_type: str,
        priority: Priority = Priority.NORMAL,
        payload: Optional[Dict] = None,
        timestamp: Optional[int] = None
    ) -> tuple[bool, str]:
        """
        Add item to queue. Returns (success, message).
        
        For burst events:
        - Checks rate limiting
        - Immediately processes if possible
        - Notifies WebSocket clients
        """
        item = AvatarQueueItem(
            user_id=user_id,
            event_type=event_type,
            priority=priority,
            payload=payload,
            timestamp=timestamp
        )
        
        async with self._lock:
            # Check rate limiting for burst events
            if priority == Priority.BURST:
                if not self.can_burst(user_id):
                    remaining = self.get_burst_cooldown_remaining(user_id)
                    return False, f"Rate limited. Try again in {remaining:.1f}s"
                
                # Record burst timestamp
                self._burst_timestamps[user_id] = time.time()
                
                # For burst: immediate processing, skip queue
                logger.info(f"🚨 BURST TRIGGER: {event_type} for user {user_id}")
                await self._notify_ws("burst_trigger", {
                    "user_id": user_id,
                    "event_type": event_type,
                    "priority": priority.value,
                    "payload": payload,
                    "timestamp": timestamp,
                    "immediate": True
                })
                
                # Process immediately in background
                asyncio.create_task(self._process_burst_item(item))
                return True, "Burst event processed immediately"
            
            # Normal priority: add to queue
            # Lower priority value = higher priority (0 for burst, 1 for normal)
            priority_value = 0 if priority == Priority.BURST else 1
            await self._queue.put((priority_value, time.time(), item))
            
            await self._notify_ws("queue_added", {
                "user_id": user_id,
                "event_type": event_type,
                "priority": priority.value,
                "queue_position": self._queue.qsize()
            })
            
            return True, f"Added to queue (position: {self._queue.qsize()})"
    
    async def _process_burst_item(self, item: AvatarQueueItem):
        """Process a burst item immediately"""
        self._current_item = item
        try:
            # Here you would trigger the actual avatar response
            # For now, we simulate the processing
            logger.info(f"Processing burst: {item.event_type} for user {item.user_id}")
            
            # Notify that burst is being processed
            await self._notify_ws("burst_processing", {
                "user_id": item.user_id,
                "event_type": item.event_type,
                "payload": item.payload
            })
            
            # Simulate avatar generation/processing time
            await asyncio.sleep(0.5)
            
            # Notify completion
            await self._notify_ws("burst_complete", {
                "user_id": item.user_id,
                "event_type": item.event_type,
                "success": True
            })
            
        except Exception as e:
            logger.error(f"Error processing burst item: {e}")
            await self._notify_ws("burst_error", {
                "user_id": item.user_id,
                "event_type": item.event_type,
                "error": str(e)
            })
        finally:
            self._current_item = None
    
    async def process_queue(self):
        """Main queue processing loop"""
        self._processing = True
        while self._processing:
            try:
                # Wait for items (with timeout to allow checking _processing flag)
                priority_value, enqueue_time, item = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
                
                self._current_item = item
                
                # Process the item
                await self._process_normal_item(item)
                
                self._queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in queue processing: {e}")
                
        self._current_item = None
    
    async def _process_normal_item(self, item: AvatarQueueItem):
        """Process a normal priority queue item"""
        try:
            logger.info(f"Processing normal: {item.event_type} for user {item.user_id}")
            
            await self._notify_ws("processing", {
                "user_id": item.user_id,
                "event_type": item.event_type,
                "priority": "normal"
            })
            
            # Simulate processing time
            await asyncio.sleep(2.0)
            
            await self._notify_ws("complete", {
                "user_id": item.user_id,
                "event_type": item.event_type,
                "success": True
            })
            
        except Exception as e:
            logger.error(f"Error processing normal item: {e}")
    
    def get_queue_status(self, user_id: Optional[int] = None) -> Dict:
        """Get current queue status"""
        # Note: asyncio.Queue doesn't support peeking, so this is approximate
        return {
            "queue_size": self._queue.qsize(),
            "is_processing": self._current_item is not None,
            "current_item": {
                "user_id": self._current_item.user_id,
                "event_type": self._current_item.event_type,
                "priority": self._current_item.priority.value
            } if self._current_item else None,
            "burst_rate_limit": {
                "window_seconds": self._burst_rate_limit_seconds,
                "active_limits": len(self._burst_timestamps)
            }
        }
    
    def stop(self):
        """Stop the queue processor"""
        self._processing = False


# Global singleton instance
avatar_queue = AvatarQueue()
