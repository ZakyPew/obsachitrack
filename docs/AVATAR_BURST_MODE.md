# Avatar Burst Mode Integration Guide

## Overview

The Avatar Burst Mode API allows the StreamTracker avatar to receive immediate "interrupt" triggers when big moments are detected via audio analysis. This bypasses the normal screenshot interval queue for instant reactions.

## Features

- **Immediate Processing**: Burst events skip the queue and process instantly
- **Rate Limiting**: Max 1 burst per 5 seconds to prevent spam
- **WebSocket Support**: Real-time updates via `/avatar/ws`
- **Event Logging**: All burst events stored in database
- **Priority Queue**: Normal and burst priority levels

## API Endpoints

### POST /avatar/burst-trigger

Trigger an immediate avatar response for a detected audio event.

**Headers:**
```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "event_type": "achievement",
  "confidence": 0.95,
  "timestamp": 1712534400000,
  "game_context": "Counter-Strike 2"
}
```

**Event Types:**
- `achievement` - Achievement unlocked
- `death` - Player death detected
- `killstreak` - Multiple kills in succession
- `explosion` - Loud explosion sound detected

**Response (Success):**
```json
{
  "success": true,
  "message": "Burst event processed immediately",
  "event_id": 123
}
```

**Response (Rate Limited):**
```json
{
  "success": false,
  "message": "Rate limited. Try again in 3.5s",
  "event_id": 124,
  "cooldown_remaining": 3.5
}
```

### GET /avatar/queue-status

Get current queue status.

**Response:**
```json
{
  "queue_size": 3,
  "is_processing": true,
  "current_item": {
    "user_id": 1,
    "event_type": "killstreak",
    "priority": "burst"
  },
  "burst_rate_limit": {
    "window_seconds": 5.0,
    "active_limits": 2
  }
}
```

### GET /avatar/burst-history

Get burst event history.

**Query Parameters:**
- `limit` (optional): Number of events to return (default: 50)

**Response:**
```json
{
  "events": [
    {
      "id": 123,
      "event_type": "achievement",
      "confidence": 0.95,
      "timestamp": 1712534400000,
      "game_context": "Counter-Strike 2",
      "processed": true,
      "created_at": "2026-04-01T23:36:00"
    }
  ],
  "count": 1
}
```

## WebSocket: /avatar/ws

Connect for real-time updates instead of polling.

**Connection URL:**
```
ws://host:port/avatar/ws?token=YOUR_API_KEY
```

### Events (Server → Client)

**connected**
```json
{
  "type": "connected",
  "user_id": 1,
  "username": "SteamUser"
}
```

**burst_trigger**
```json
{
  "type": "burst_trigger",
  "data": {
    "user_id": 1,
    "event_type": "killstreak",
    "priority": "burst",
    "immediate": true
  }
}
```

**burst_processing**
```json
{
  "type": "burst_processing",
  "data": {
    "user_id": 1,
    "event_type": "killstreak"
  }
}
```

**burst_complete**
```json
{
  "type": "burst_complete",
  "data": {
    "user_id": 1,
    "event_type": "killstreak",
    "success": true
  }
}
```

### Commands (Client → Server)

**Ping:**
```json
{"type": "ping"}
```

**Get Status:**
```json
{"type": "get_status"}
```

## Integration Example (Python)

```python
import requests
import asyncio
import websockets
import json

API_KEY = "your_api_key"
BASE_URL = "http://localhost:8000"

def trigger_burst(event_type, confidence, game_context=None):
    """Send burst trigger to avatar"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "event_type": event_type,
        "confidence": confidence,
        "timestamp": int(time.time() * 1000),
        "game_context": game_context
    }
    
    resp = requests.post(
        f"{BASE_URL}/avatar/burst-trigger",
        headers=headers,
        json=payload
    )
    return resp.json()

# Example: Audio detection triggers burst
if audio_detected_explosion(confidence=0.92):
    result = trigger_burst("explosion", 0.92, "Counter-Strike 2")
    if result["success"]:
        print("Avatar triggered!")
    else:
        print(f"Rate limited: {result['cooldown_remaining']}s remaining")
```

## Audio Detection Integration

Connect your audio detection system to the burst trigger:

```python
# In your audio event detection code:
async def on_audio_event(event_type, confidence):
    if confidence > 0.8:  # High confidence threshold
        await trigger_burst(event_type, confidence)
```

## Database Schema

The migration adds two tables:

### burst_events
Logs all audio-detected events.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | User who triggered |
| event_type | VARCHAR | Type of event |
| confidence | REAL | 0.0-1.0 confidence score |
| timestamp | INTEGER | Unix ms from client |
| game_context | VARCHAR | Optional game context |
| processed | BOOLEAN | Whether processed |
| created_at | DATETIME | Server timestamp |

### avatar_queue
Persistent queue for tracking jobs (optional).

## Rate Limiting

- **Window**: 5 seconds per user
- **Applies to**: Burst priority events only
- **Normal queue**: No rate limiting

## Testing

Run the test script:

```bash
cd backend
python test_burst_mode.py YOUR_API_KEY
```

## Files Added/Modified

### New Files:
- `backend/routers/avatar.py` - Avatar API routes
- `backend/services/avatar_queue.py` - Queue management
- `backend/migrations/001_add_burst_events.sql` - DB migration
- `backend/test_burst_mode.py` - Test script
- `docs/AVATAR_BURST_MODE.md` - This document

### Modified:
- `backend/main.py` - Added avatar router + lifespan
- `backend/database.py` - Added BurstEvent and AvatarQueueItem models
- `backend/services/__init__.py` - Package exports
- `backend/routers/__init__.py` - Package exports

## Next Steps

1. Run the database migration
2. Start the server: `python backend/main.py`
3. Get an API key from your user account
4. Connect your audio detection system
5. Test with the provided test script
