#!/usr/bin/env python3
"""
StreamTracker Windows Build Script 🎀
Creates standalone .exe for Windows release
"""

import PyInstaller.__main__
import os
import sys
import shutil

print("=" * 60)
print("🎀 StreamTracker Windows Build")
print("=" * 60)

# Clean previous builds
print("\n🧹 Cleaning previous builds...")
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"  Removed {folder}/")

# PyInstaller arguments
print("\n📦 Building executable...")
print("  This may take a few minutes...")
print()

args = [
    'app.py',                          # Main script
    '--name=StreamTracker',            # Output name
    '--onefile',                       # Single .exe file
    '--windowed',                      # No console window (GUI mode)
    '--icon=assets/icon.ico',          # App icon (if exists)
    
    # Include data files
    '--add-data=index.html:.',
    '--add-data=dock.html:.',
    '--add-data=assets:assets',
    
    # Hidden imports (ensure these get bundled)
    '--hidden-import=websocket_server',
    '--hidden-import=streamerbot_handler',
    '--hidden-import=sound_manager',
    '--hidden-import=websockets',
    '--hidden-import=websockets.legacy',
    '--hidden-import=websockets.legacy.server',
    '--hidden-import=websockets.legacy.protocol',
    '--hidden-import=asyncio',
    
    # Flask related
    '--hidden-import=flask',
    '--hidden-import=flask_cors',
    '--hidden-import=werkzeug',
    '--hidden-import=jinja2',
    '--hidden-import=markupsafe',
    
    # Other dependencies
    '--hidden-import=requests',
    '--hidden-import=PIL',
    '--hidden-import=PIL.Image',
    '--hidden-import=psutil',
    
    # Optimize
    '--strip',
    '--noupx',
    
    # Output
    '--distpath=dist',
    '--workpath=build',
    '--specpath=.',
]

# Run PyInstaller
PyInstaller.__main__.run(args)

print("\n" + "=" * 60)
print("✅ Build Complete!")
print("=" * 60)
print("\nOutput: dist/StreamTracker.exe")
print("\nTo distribute:")
print("  1. Create StreamTracker_v1.6.zip")
print("  2. Include: StreamTracker.exe, README.md")
print("  3. Test on clean Windows VM")
print("\nMade for Daddy with love 🎀💕")
