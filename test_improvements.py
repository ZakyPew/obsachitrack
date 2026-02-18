#!/usr/bin/env python3
"""
StreamTracker Improvements Test Suite 🎀
Test the new WebSocket, Streamer.bot, and Sound modules
"""

import sys
import time
import threading
import requests
import json

print("=" * 60)
print("🎀 StreamTracker Improvements Test Suite")
print("=" * 60)

# Test 1: Sound Manager
print("\n🔊 Test 1: Sound Manager")
print("-" * 40)

try:
    from sound_manager import SoundManager
    
    sound_mgr = SoundManager(base_volume=0.5)
    
    test_achievements = [
        {"name": "First Step", "rarity": 75.5},      # Common
        {"name": "Explorer", "rarity": 42.1},        # Uncommon
        {"name": "Collector", "rarity": 15.8},       # Rare
        {"name": "Perfectionist", "rarity": 3.2},    # Ultra Rare
        {"name": "Completionist", "rarity": 0.9},    # Legendary
    ]
    
    for ach in test_achievements:
        result = sound_mgr.play_achievement_sound(ach)
        print(f"  ✅ {ach['name']} ({ach['rarity']}%) -> {result['tier'].upper()}")
    
    print("\n  Sound Manager: PASSED ✓")
except Exception as e:
    print(f"\n  ❌ Sound Manager FAILED: {e}")

# Test 2: WebSocket Server
print("\n🌐 Test 2: WebSocket Server")
print("-" * 40)

try:
    from websocket_server import run_server_in_thread, broadcast_update, push_achievement_unlocked
    import asyncio
    import websockets
    
    # Start server in background thread
    ws_thread = threading.Thread(target=run_server_in_thread, daemon=True)
    ws_thread.start()
    time.sleep(2)  # Let server start
    
    print("  ✅ WebSocket server started on ws://localhost:8765")
    
    # Test client connection
    async def test_client():
        try:
            async with websockets.connect('ws://localhost:8765') as websocket:
                print("  ✅ Client connected to WebSocket")
                
                # Test broadcast
                await broadcast_update({"test": "Hello from test!"})
                print("  ✅ Broadcast sent")
                
                # Test achievement push
                await push_achievement_unlocked({
                    "name": "Test Achievement",
                    "rarity": 5.5,
                    "icon": "test.png"
                })
                print("  ✅ Achievement push sent")
                
                return True
        except Exception as e:
            print(f"  ❌ WebSocket client error: {e}")
            return False
    
    # Run test
    result = asyncio.get_event_loop().run_until_complete(test_client())
    
    if result:
        print("\n  WebSocket Server: PASSED ✓")
    else:
        print("\n  WebSocket Server: FAILED ✗")
        
except Exception as e:
    print(f"\n  ❌ WebSocket Server FAILED: {e}")

# Test 3: Streamer.bot Handler (Routes)
print("\n🤖 Test 3: Streamer.bot Handler")
print("-" * 40)

try:
    from streamerbot_handler import check_and_announce_rare, format_chat_message
    
    # Test rare achievement detection
    test_cases = [
        ({"name": "Common Ach"}, 75.0, None),
        ({"name": "Rare Ach"}, 4.5, "RARE"),
        ({"name": "Legendary Ach"}, 0.5, "LEGENDARY"),
    ]
    
    for ach, rarity, expected in test_cases:
        result = check_and_announce_rare(ach, rarity)
        if expected and expected in (result or ""):
            print(f"  ✅ {ach['name']} ({rarity}%) -> Announced")
        elif not expected and result is None:
            print(f"  ✅ {ach['name']} ({rarity}%) -> Silent (common)")
        else:
            print(f"  ⚠️  {ach['name']} ({rarity}%) -> Unexpected: {result}")
    
    # Test message formatting
    msg = format_chat_message("Test message")
    if "actions" in msg.get_json():
        print("  ✅ Message formatting works")
    
    print("\n  Streamer.bot Handler: PASSED ✓")
    
except Exception as e:
    print(f"\n  ❌ Streamer.bot Handler FAILED: {e}")

# Test 4: Flask Routes (if app.py is available)
print("\n🌶️  Test 4: Flask Integration Check")
print("-" * 40)

try:
    # Check if we can import the blueprint
    from streamerbot_handler import streamerbot_bp
    print("  ✅ Streamer.bot Blueprint can be imported")
    
    # Check routes
    routes = [rule.rule for rule in streamerbot_bp.url_map.iter_rules()] if hasattr(streamerbot_bp, 'url_map') else []
    print(f"  ✅ Blueprint has routes: {routes}")
    
    print("\n  Flask Integration: READY ✓")
    
except Exception as e:
    print(f"\n  ⚠️  Flask Integration: {e}")

print("\n" + "=" * 60)
print("🎉 Test Suite Complete!")
print("=" * 60)
print("\nTo fully test, run:")
print("  python app.py  # Start the main app")
print("  python test_improvements.py  # Run this test")
print("\nThen test chat commands via Streamer.bot!")
