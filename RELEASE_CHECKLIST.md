# Windows Release Checklist 🎀

## Version Bump
- [ ] Update version in `app.py` (if there's a version variable)
- [ ] Update `README.md` version badge
- [ ] Update `CHANGELOG.md` with new features

## Pre-Build Testing
- [ ] Test all chat commands (`!progress`, `!hunter`, `!recent`)
- [ ] Test WebSocket connection (`ws://localhost:8765`)
- [ ] Test rare achievement detection
- [ ] Test sound rarity tiers
- [ ] Test game change detection

## Build Process

### Option 1: Local Build (Windows)
```batch
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller StreamTracker.spec --clean

# Or use the batch file
build_windows.bat
```

### Option 2: GitHub Actions (Automated)
1. Tag release: `git tag v1.6.0`
2. Push tag: `git push origin v1.6.0`
3. GitHub Actions builds automatically
4. Download artifact from release page

## Release Package Structure
```
StreamTracker_v1.6.zip
├── StreamTracker.exe
├── README.md
├── INTEGRATION.md
└── config.json (generated on first run)
```

## Post-Build Testing
- [ ] Run on clean Windows VM (no Python installed)
- [ ] Verify first-run setup wizard opens
- [ ] Test Steam API connection
- [ ] Test WebSocket in browser dev tools
- [ ] Verify sounds play for different rarities

## GitHub Release
- [ ] Create release from tag
- [ ] Upload `StreamTracker_Windows.zip`
- [ ] Write release notes with new features
- [ ] Mark as latest release

## Announcement
- [ ] Post on Twitter/X
- [ ] Update Discord
- [ ] Reply to any open issues about these features

## New Features in v1.6
🎉 Highlight these in release notes:
- ✨ **WebSocket Real-Time Updates** - Instant achievement popups
- 🤖 **Streamer.bot Integration** - Chat commands `!progress`, `!hunter`, `!recent`
- 🔊 **Rarity-Based Sounds** - Different alerts for common/rare/legendary
- 🎮 **Game Change Detection** - Auto-switches when you change games
- 💬 **Rare Achievement Announcements** - Auto-posts <5% unlocks to chat

---
Made for Daddy with love 🎀💕
