# PROJECT_MEM.md

**Project:** StreamTracker Web (SaaS Platform)  
**Created:** 2026-03-01  
**Last Updated:** 2026-03-03  
**Location:** `~/projects/active/streamtracker-web/`  
**Status:** 🚀 **PRODUCTION READY - LAUNCH DAY**  

---

## 🎯 Current Goal

Transform the local StreamTracker desktop app (Flask-based, v1.7) into a **web-based SaaS service** with:
- User accounts (Steam SSO)
- API key management
- Cloud-based achievement tracking
- Browser overlay (OBS integration)
- Premium features (Stripe billing)

---

## ✅ Completed

### 2026-03-01 — Project Bootstrap
- [x] Cloned original StreamTracker repo (`ZakyPew/StreamTracker`)
- [x] Created `ARCHITECTURE.md` with system design
- [x] Set up project structure:
  - `backend/` — FastAPI structure
  - `frontend/` — Web overlay
  - `improvements/` — Test scripts

### Original StreamTracker Features (v1.7)
- [x] WebSocket real-time updates (`localhost:8765`)
- [x] Streamer.bot integration — chat commands (`!progress`, `!hunter`, `!recent`)
- [x] Rarity-based sound alerts (5 tiers: Common → Legendary)
- [x] Auto-theme matching (chameleon colors from Steam artwork)
- [x] Hunter Mode (pin locked achievements)
- [x] Vertical mode for TikTok/Shorts
- [x] OBS Dock for control
- [x] Game change detection

---

## ✅ Recent Fixes & Features (2026-03-02)

### Steam API Key Save Fix
- **Fixed:** Steam API key not saving due to database session mismatch
- **Solution:** Use fresh `SessionLocal()` in save endpoint, re-fetch user in that session
- **Status:** ✅ DONE

### Game Name Override System
- **Feature:** Users can now rename games when Steam API returns wrong/internal names
- **Implementation:**
  - `UserGameName` model - per-user custom names
  - `GlobalGameName` model - admin-curated global overrides
  - Priority: User override > Global override > Steam API name
- **API Endpoints:**
  - `POST /api/game-name-override` - Set custom name
  - `DELETE /api/game-name-overrides/{app_id}` - Remove override
  - `GET /api/game-name-overrides/{app_id}` - Get override status
  - `GET /api/game-name-overrides` - List all overrides
- **Status:** ✅ DONE

### Admin Panel (Steam ID Gated)
- **Access:** Gated by `ADMIN_STEAM_IDS` env var (your Steam ID)
- **Features:** Manage global game name overrides, user management (grant/revoke premium, admin, VIP)
- **URL:** `/admin`
- **Status:** ✅ DONE (bug fixes completed 2026-03-03)

### Launch Day Visual Updates (2026-03-03)
- **Real Screenshots:** ARC RAIDERS, Final Fantasy XVI, FAITH overlays on landing page
- **Logo:** Custom logo as favicon and navbar icon
- **Steam Buttons:** Custom SVG high-resolution buttons matching Steam brand colors
- **Tracking:** Google AdSense + Google Analytics 4 integrated

### Overlay with Game Artwork
- **Style:** Matches original StreamTracker GitHub design
- **Features:** Steam card, progress bar, recent unlocks tray, "LATEST UNLOCK" display
- **Artwork:** Game header images from Steam Store API with blur effect
- **Status:** ✅ DONE

## 🔄 In Progress

- [x] FastAPI backend with Steam OAuth ✅ DONE
- [x] Database models ✅ DONE  
- [x] Cloud overlay HTML ✅ DONE
- [x] Game name override system ✅ DONE
- [x] Admin panel (Steam ID gated) ✅ DONE
- [x] Game artwork in overlay ✅ DONE
- [x] Dashboard UI for game renaming ✅ DONE
- [x] Vertical overlay mode (Premium) ✅ DONE
- [x] Stripe integration backend ✅ DONE
- [x] Stripe activation ✅ DONE
- [x] Google AdSense monetization ✅ DONE
- [x] Google Analytics 4 tracking ✅ DONE
- [x] Landing page with real screenshots ✅ DONE
- [x] Custom Steam sign-in buttons ✅ DONE
- [x] Logo and favicon ✅ DONE
- [ ] Dashboard premium checkout UI polish

---

## 📝 Key Decisions

1. **Backend:** FastAPI (async, modern, auto-docs)
2. **Auth:** Steam OpenID (users already have Steam accounts)
3. **Database:** PostgreSQL (user data) + Redis (caching/sessions)
4. **Frontend:** Vanilla JS overlay (OBS-friendly) + React dashboard (optional)
5. **Billing:** Stripe (monthly subscriptions, free tier limits)

---

## 🔧 Technical Notes

### File Locations
| Component | Path |
|-----------|------|
| Original Flask app | `app.py` |
| Backend entry | `backend/main.py` |
| Steam auth | `backend/auth/steam.py` |
| Database setup | `backend/database.py` |
| WebSocket server | `websocket_server.py` (reuse!) |
| Sound manager | `sound_manager.py` (reuse!) |
| Streamer.bot handler | `streamerbot_handler.py` (reuse!) |

### Original App Endpoints (Port These!)
- `GET /` — Main overlay
- `GET /dock` — Control dock
- `GET /data` — Achievement data (JSON)
- `POST /webhook/streamerbot` — Streamer.bot integration
- `WS localhost:8765` — WebSocket real-time updates

### Git
- **Repo:** Local (based on `ZakyPew/StreamTracker`)
- **Branch:** master
- **Status:** 12 commits, clean working tree

---

## 🐛 Known Issues / Blockers

- ✅ All blockers resolved! StreamTracker v1.0 is production ready.

## 🚀 Launch Checklist

- [x] Site live at streamtracker.cloud
- [x] SSL certificate active
- [x] Database backups configured
- [x] AdSense integrated
- [x] Analytics tracking
- [x] Admin panel functional
- [x] Stripe billing working
- [x] Real product screenshots on landing page
- [ ] Social media announcement
- [ ] First paying customer

---

## 💡 Ideas / Backlog

- [ ] Free tier: 1 game, basic overlay
- [ ] Premium: Unlimited games, custom themes, priority WebSocket
- [ ] Analytics dashboard (streaming stats, achievement history)
- [ ] Public API for 3rd party integrations
- [ ] Mobile app for notifications?

---

## 🔗 References

- **Original Repo:** https://github.com/ZakyPew/StreamTracker
- **Architecture:** `ARCHITECTURE.md`
- **Release Checklist:** `RELEASE_CHECKLIST.md`
- **Integration Guide:** `INTEGRATION.md`

---

*Last updated: 2026-03-03 — PRODUCTION READY FOR LAUNCH! 🚀*
