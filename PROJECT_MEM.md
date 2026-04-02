# PROJECT_MEM.md

**Project:** StreamTracker Web (SaaS Platform)  
**Created:** 2026-03-01  
**Last Updated:** 2026-03-07  
**Location:** `~/projects/active/streamtracker-web/`  
**Status:** 🚀 **ACTIVE - 23 PRs MERGED**

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

## ✅ Recent PRs Merged (March 5-7, 2026)

### PR #64 — Steam Game Override Flow
**Forced Steam game override (DB, API, overlay, dashboard)**
- Users can manually override detected Steam game
- `ForcedGameOverride` model + `forced_game_overrides` table
- API endpoints: `POST/GET/DELETE /api/forced-game-override`
- Overlay respects override when rendering
- Dashboard UI for setting/clearing override

### PR #63 — Discord Links Update
**Updated all Discord invite links to new URL**
- Changed Discord invite URLs across all pages

### PR #62 — Dashboard Current-Game Polling
**Polling with cleanup and empty-state**
- 20s polling interval for active Steam game state
- Empty-state placeholder when no game is active
- Cleanup on pagehide/logout to prevent duplicate intervals
- Hunter controls update automatically when game changes

### PR #21 — Sticky Quick-Nav
- Sticky navigation bar for dashboard
- Improved mobile UX

### PR #20 — Pro Capability Audit + Waitlist Gating
- `PLAN_PRO_AUDIT` map for Pro features
- Waitlist form when Pro checkout disabled
- Pro Preview Lab section in dashboard
- Pricing value statements (outcome-oriented)

### PR #19 — Lifecycle Milestone Tracking
- `LifecycleEvent` + `InAppNotification` models
- Milestone tracking: account created, Steam key connected, overlay URL generated
- Dashboard checklist: "Complete setup" + upgrade prompts
- `GET /api/dashboard-milestones` endpoint

### PR #18 — SEO + Open Graph + JSON-LD
- Meta tags, canonical links
- Open Graph + Twitter card tags
- JSON-LD structured data on pricing page
- Root `/` serves landing page directly

### PR #17 — Pricing Auth-Aware CTAs
- Billing interval options (monthly/quarterly/annual)
- Unauthenticated users → login with intent
- Authenticated users → direct checkout
- `GET /stripe/pricing-options` endpoint

### PR #16 — Analytics for CTAs + Stripe Webhooks
- Client-side events: `landing_cta_click`, `pricing_plan_cta_click`, `begin_checkout`, `purchase`
- Server-side webhook logging for conversions
- Checkout success/cancel tracking

### PR #15 — Dashboard UI Revamp
- Modern Inter font, gradients, sticky navbar
- API Key & Account ID Guide panel
- Per-platform help (Steam/Xbox/PlayStation)
- Inline help box for linking

### PR #14 + #13 + #12 — Landing Page Live Preview
- Rotating game preview overlay on landing page
- `GET /api/landing-preview` (JSON snapshot)
- `GET /api/landing-preview/stream` (SSE real-time updates)
- Client-side rotation every ~2.6s with dot indicators

### PR #11 — Dashboard Modernization
- Revamped dashboard styling
- Trophy room link improvements
- Linked accounts UI polish

---

## ✅ Earlier Features (March 1-3)

### Steam API Key Save Fix
- **Fixed:** Steam API key not saving due to database session mismatch
- **Solution:** Use fresh `SessionLocal()` in save endpoint

### Game Name Override System
- `UserGameName` + `GlobalGameName` models
- Priority: User > Global > Steam API

### Admin Panel (Steam ID Gated)
- `/admin` — Manage game name overrides, user management

### Launch Day Visual Updates
- Real overlay screenshots (ARC RAIDERS, FF16, FAITH)
- Custom logo as favicon/navbar icon
- Custom Steam sign-in buttons (SVG)
- Google AdSense + Analytics 4

---

## 🔄 In Progress

- [x] FastAPI backend with Steam OAuth ✅ DONE
- [x] Database models ✅ DONE  
- [x] Cloud overlay HTML ✅ DONE
- [x] Game name override system ✅ DONE
- [x] Admin panel (Steam ID gated) ✅ DONE
- [x] Game artwork in overlay ✅ DONE
- [x] Dashboard UI ✅ DONE
- [x] Vertical overlay mode (Premium) ✅ DONE
- [x] Stripe integration ✅ DONE
- [x] Google AdSense + Analytics ✅ DONE
- [x] Landing page live preview ✅ DONE
- [x] Lifecycle milestone tracking ✅ DONE
- [x] Pro waitlist gating ✅ DONE
- [x] SEO/Open Graph metadata ✅ DONE
- [x] Dashboard current-game polling ✅ PR #62
- [x] Discord invite links updated ✅ PR #63
- [x] Steam game override flow ✅ PR #64
- [ ] Social media announcement
- [ ] First paying customer

---

## 📝 Key Decisions

1. **Backend:** FastAPI (async, modern, auto-docs)
2. **Auth:** Steam OpenID (users already have Steam accounts)
3. **Database:** PostgreSQL (user data) + Redis (caching/sessions)
4. **Frontend:** Vanilla JS overlay (OBS-friendly)
5. **Billing:** Stripe with monthly/quarterly/annual options

---

## 🔧 Technical Notes

### File Locations
| Component | Path |
|-----------|------|
| Backend | `main.py` |
| Stripe routes | `routers/stripe.py` |
| Auth | `auth/steam.py`, `auth/local.py` |
| Services | `services/lifecycle.py`, `services/entitlements.py` |

### Git
- **Repo:** `ZakyPew/StreamTrackerWebsite`
- **Branch:** master
- **Total PRs Merged:** 21+ (#11-#21, more in flight)

---

## 🐛 Known Issues / Blockers

- ✅ No major blockers

---

## 🚀 Launch Checklist

- [x] Site live at streamtracker.cloud
- [x] SSL certificate active
- [x] Database backups configured
- [x] AdSense integrated
- [x] Analytics tracking
- [x] Admin panel functional
- [x] Stripe billing working
- [x] Real product screenshots on landing page
- [x] Live preview on landing page
- [x] Lifecycle tracking + upgrade prompts
- [ ] Social media announcement
- [ ] First paying customer

---

## 💡 Ideas / Backlog

- [ ] Free tier: 1 game, basic overlay
- [ ] Premium: Unlimited games, custom themes
- [ ] Twitch integration (mentioned in earlier notes)
- [ ] Nintendo Switch integration (mentioned in earlier notes)
- [ ] Analytics dashboard (streaming stats)
- [ ] Public API for 3rd party integrations

---

## 🔗 References

- **Repo:** https://github.com/ZakyPew/StreamTrackerWebsite
- **Live Site:** https://streamtracker.cloud
- **VPS:** 74.208.147.236:/opt/streamtracker/

---

*Last updated: 2026-03-07 — PRs #62, #63, #64 deployed 🚀*

---

## 🛠️ Tech Stack
- Next.js 14
- FastAPI
- PostgreSQL
- Prisma ORM
- TypeScript
- TailwindCSS
- WebSocket
- Stripe Billing
- Steam OAuth

## 🔗 Related Projects
- stream-bot (shared OBS/WebSocket patterns)
- vtuber (streaming ecosystem)
