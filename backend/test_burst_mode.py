"""
Test script for Avatar Burst Mode API

This demonstrates how to use the burst trigger endpoint and WebSocket connection.
"""
import asyncio
import websockets
import aiohttp
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/avatar/ws"
API_KEY = "your_api_key_here"  # Replace with actual API key


async def test_burst_trigger():
    """Test the burst trigger HTTP endpoint"""
    print("🧪 Testing burst trigger endpoint...")
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "event_type": "achievement",
            "confidence": 0.95,
            "timestamp": 1712534400000,  # Example unix_ms
            "game_context": "Counter-Strike 2"
        }
        
        async with session.post(
            f"{BASE_URL}/avatar/burst-trigger",
            headers=headers,
            json=payload
        ) as resp:
            result = await resp.json()
            print(f"Status: {resp.status}")
            print(f"Response: {json.dumps(result, indent=2)}")
            return result


async def test_burst_rate_limit():
    """Test rate limiting (should fail on 2nd request)"""
    print("\n🧪 Testing burst rate limiting...")
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "event_type": "killstreak",
            "confidence": 0.88,
            "timestamp": 1712534400000
        }
        
        # First request should succeed
        print("  → Sending first burst...")
        async with session.post(
            f"{BASE_URL}/avatar/burst-trigger",
            headers=headers,
            json=payload
        ) as resp:
            result1 = await resp.json()
            print(f"  First: {result1['message']}")
        
        # Second request should be rate limited
        print("  → Sending second burst immediately...")
        async with session.post(
            f"{BASE_URL}/avatar/burst-trigger",
            headers=headers,
            json=payload
        ) as resp:
            result2 = await resp.json()
            print(f"  Second: {result2['message']}")
            if not result2['success']:
                print(f"  ✓ Rate limiting works! Cooldown: {result2.get('cooldown_remaining', 0):.1f}s")


async def test_queue_status():
    """Test queue status endpoint"""
    print("\n🧪 Testing queue status...")
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        async with session.get(
            f"{BASE_URL}/avatar/queue-status",
            headers=headers
        ) as resp:
            result = await resp.json()
            print(f"Queue status: {json.dumps(result, indent=2)}")


async def test_burst_history():
    """Test burst history endpoint"""
    print("\n🧪 Testing burst history...")
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        async with session.get(
            f"{BASE_URL}/avatar/burst-history?limit=10",
            headers=headers
        ) as resp:
            result = await resp.json()
            print(f"History ({result['count']} events):")
            for event in result['events'][:5]:
                print(f"  - {event['event_type']} (confidence: {event['confidence']})")


async def test_websocket():
    """Test WebSocket connection for real-time updates"""
    print("\n🧪 Testing WebSocket connection...")
    
    ws_url = f"{WS_URL}?token={API_KEY}"
    
    try:
        async with websockets.connect(ws_url) as ws:
            # Receive connection confirmation
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"Connected: {data}")
            
            # Send a ping
            await ws.send(json.dumps({"type": "ping"}))
            pong = await ws.recv()
            print(f"Ping test: {pong}")
            
            # Request status
            await ws.send(json.dumps({"type": "get_status"}))
            status_msg = await ws.recv()
            print(f"Status: {status_msg}")
            
            # Keep connection open briefly to catch any burst events
            print("  → Listening for events (5s)...")
            try:
                await asyncio.wait_for(ws.recv(), timeout=5.0)
            except asyncio.TimeoutError:
                print("  (No events received)")
                
    except Exception as e:
        print(f"WebSocket error: {e}")


async def main():
    """Run all tests"""
    print("=" * 50)
    print("🎀 Avatar Burst Mode API Tests")
    print("=" * 50)
    
    await test_burst_trigger()
    await asyncio.sleep(1)
    await test_burst_rate_limit()
    await asyncio.sleep(6)  # Wait for rate limit to reset
    await test_queue_status()
    await test_burst_history()
    await test_websocket()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        API_KEY = sys.argv[1]
    else:
        print("Usage: python test_burst_mode.py <API_KEY>")
        print("Using default placeholder key (tests will fail auth)")
    
    asyncio.run(main())
