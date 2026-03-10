# StreamTracker Overlay Studio - PRO Feature Specification

## Overview
Build a professional overlay studio for StreamTracker that allows streamers to design, customize, and deploy custom overlays using StreamTracker's unique Xbox and achievement data. This is a **PRO/BETA tier feature** while keeping the existing overlay as the default option.

**Inspired by:** StreamCopilot.app overlay templates

---

## Core Concept

StreamTracker's advantage is **Xbox/achievement sync data**. The Overlay Studio lets streamers build custom overlays that display:
- Current game being played (Xbox integration)
- Achievement progress and unlocks
- Gamerscore
- Recently unlocked achievements
- Achievement hunting progress
- Completion percentage
- And more...

All with professional templates, drag-and-drop editor, and real-time preview.

---

## Feature Scope

### Tier: PRO/BETA
- **Status:** Beta feature for PRO users
- **Default:** Existing overlay remains default for all users
- **Access:** `/studio` route or "Pro Studio" button in dashboard

---

## User Flow

```
1. User visits StreamTracker Dashboard
   ↓
2. Clicks "Pro Studio" (PRO badge)
   ↓
3. Lands on Template Gallery
   ↓
4. Chooses template or starts blank
   ↓
5. Enters Visual Editor
   ↓
6. Adds Xbox/Achievement data widgets
   ↓
7. Customizes styling (colors, fonts, animations)
   ↓
8. Saves overlay
   ↓
9. Gets OBS URL / Browser Source link
   ↓
10. Overlay updates in real-time with achievement data
```

---

## Template Gallery (Launch Templates)

### 1. Achievement Hunter
**Purpose:** For achievement hunters tracking progress
**Elements:**
- Current game title with box art
- Gamerscore display
- Progress bar for current achievement
- Recent unlocks list (last 3)
- Completion percentage

### 2. Speedrun Tracker
**Purpose:** Speedrunners tracking splits and achievements
**Elements:**
- Timer/splits widget
- Current level/stage
- Achievement unlock alerts (large)
- Personal best comparison

### 3. Retro Completionist
**Purpose:** Retro gamers showing collection progress
**Elements:**
- Retro game box art (nostalgic styling)
- Completion badges
- Rare achievement highlights
- Total games completed counter

### 4. Minimal Clean
**Purpose:** Subtle, professional overlay
**Elements:**
- Small corner widget
- Just game title + current achievement
- Gamerscore only
- Fade animations

### 5. Celebration Mode
**Purpose:** Big celebration for rare achievements
**Elements:**
- Full-screen achievement reveal animation
- Confetti/particle effects
- Achievement art showcase
- Sound effect triggers (optional)

### 6. Blank Canvas
**Purpose:** Power users building from scratch
**Elements:**
- Empty canvas
- Full widget library
- Grid snap system

---

## Visual Editor Features

### Canvas
- **Size:** 1920x1080 (OBS standard)
- **Background:** Transparent checkerboard pattern
- **Zoom:** 50%, 75%, 100%, 125%, 150%
- **Grid:** Toggle snap-to-grid (10px, 20px, 50px)

### Widget Library (Left Sidebar)

#### Xbox Data Widgets (Core Advantage)
| Widget | Description | Data Source |
|--------|-------------|-------------|
| `Game Title` | Current game name | Xbox API |
| `Box Art` | Game cover image | Xbox API |
| `Gamerscore` | Total GS counter | Xbox API |
| `Current Achievement` | Achievement in progress | Achievement API |
| `Progress Bar` | % to next achievement | Achievement API |
| `Recent Unlocks` | Last 3 achievements | Achievement API |
| `Rare Achievement` | Highlight rare unlocks | Achievement API |
| `Completion %` | Game completion | Achievement API |
| `Session Time` | Time played today | Xbox API |

#### Visual Elements
| Element | Description |
|---------|-------------|
| `Text` | Custom text with rich formatting |
| `Image` | Upload custom images/PNG |
| `Shape` | Rectangles, circles, rounded corners |
| `Progress Bar` | Customizable progress bars |
| `Timer` | Countdown or count-up |
| `Alert Box` | Animated notification area |

### Properties Panel (Right Sidebar)

#### Position & Size
- X, Y coordinates
- Width, Height
- Lock aspect ratio
- Rotate (degrees)

#### Styling
- Background color (solid/gradient)
- Border (width, color, radius)
- Shadow (x, y, blur, color)
- Opacity (0-100%)

#### Typography
- Font family (Google Fonts integration)
- Font size
- Font weight
- Text color
- Text shadow
- Text align

#### Animation
- Entry animation (fade, slide, bounce, etc.)
- Exit animation
- Duration
- Delay
- Loop options

#### Data Binding
- Select data source (dropdown of available data)
- Format string (e.g., "{gamerscore} GS")
- Update frequency (real-time, 5s, 30s)

---

## Data Integration

### Xbox Live API
```javascript
// Data available to widgets
{
  game: {
    title: "Halo Infinite",
    boxArt: "https://...",
    platform: "Xbox Series X"
  },
  gamerscore: {
    current: 45230,
    sessionEarned: 150
  },
  achievements: {
    current: {
      name: "Legendary",
      description: "Complete campaign on Legendary",
      progress: 75,
      total: 100,
      icon: "https://..."
    },
    recent: [...],
    rare: [...],
    completionPercent: 68.5
  },
  session: {
    startedAt: "2024-01-15T10:30:00Z",
    duration: 3600
  }
}
```

### Real-Time Updates
- WebSocket connection to StreamTracker backend
- Achievement webhook triggers
- Game change detection
- Automatic overlay refresh

---

## Technical Architecture

### Frontend Stack
- **Framework:** React 18+ (existing)
- **State:** Zustand or Redux Toolkit
- **Canvas:** Fabric.js or React-Draggable
- **Styling:** Tailwind CSS + custom CSS-in-JS for animations
- **Fonts:** Google Fonts API

### Backend Changes

#### New Database Tables
```sql
-- User overlay configurations
CREATE TABLE user_overlays (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name TEXT,
    template_id TEXT,
    config JSONB, -- Full overlay configuration
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Overlay usage analytics (for PRO metrics)
CREATE TABLE overlay_analytics (
    id UUID PRIMARY KEY,
    overlay_id UUID REFERENCES user_overlays(id),
    event_type TEXT, -- 'view', 'achievement_shown', etc.
    metadata JSONB,
    created_at TIMESTAMP
);
```

#### API Endpoints
```
GET    /api/v1/studio/templates          # List available templates
GET    /api/v1/studio/overlays           # List user's overlays
POST   /api/v1/studio/overlays           # Create new overlay
GET    /api/v1/studio/overlays/:id       # Get overlay config
PUT    /api/v1/studio/overlays/:id       # Update overlay
DELETE /api/v1/studio/overlays/:id       # Delete overlay
POST   /api/v1/studio/overlays/:id/clone # Duplicate overlay
GET    /api/v1/studio/overlays/:id/preview # Get preview image
```

### Overlay Rendering

#### Server-Side Rendering (for OBS)
- Express route: `/overlay/:userId/:overlayId`
- SSR React component
- Real-time data injection via WebSocket
- Caching: 5-second CDN cache for images

#### Client-Side Preview
- Same components as SSR
- Hot-reload on config changes
- Live data simulation mode

---

## UI/UX Design

### Studio Layout
```
┌─────────────────────────────────────────────────────────────┐
│  StreamTracker Pro Studio                    [Save] [Preview]│
├──────────┬──────────────────────────────────┬───────────────┤
│          │                                  │               │
│ WIDGETS  │         CANVAS                   │  PROPERTIES   │
│ LIBRARY  │        (1920x1080)               │   PANEL       │
│          │      ┌──────────────┐            │               │
│  [🔍]    │      │  [Game Art]  │            │ Position      │
│          │      │  [Title]     │            │   X: 100      │
│  ▸ Xbox  │      │  [Progress]  │            │   Y: 200      │
│    - Box │      └──────────────┘            │               │
│    - GS  │                                  │ Size          │
│    - Ach │  [Achievement List]              │   W: 300      │
│    - ... │                                  │   H: 150      │
│          │                                  │               │
│  ▸ Basic │                                  │ Styling       │
│    - Text│                                  │   [Color ▼]   │
│    - Img │                                  │   [Border ▼]  │
│    - ... │                                  │               │
│          │                                  │ Animation     │
│          │                                  │   [Fade In ▼] │
│          │                                  │               │
└──────────┴──────────────────────────────────┴───────────────┘
```

### Template Gallery
- Grid layout: 3 columns on desktop, 2 on tablet, 1 on mobile
- Hover: Preview animation
- Click: "Use Template" → Opens in editor
- Filter: By category (Achievement, Speedrun, Minimal, etc.)

### Editor Experience
- **Drag & Drop:** Widgets from sidebar to canvas
- **Select:** Click to select, handles appear
- **Resize:** Corner handles (respect aspect ratio if locked)
- **Move:** Drag anywhere on canvas
- **Layer:** Right-click → "Send to back/front"
- **Delete:** Select + Delete key or trash icon
- **Undo/Redo:** Ctrl+Z / Ctrl+Y (history stack)

---

## Subscription & Access Control

### Free Tier
- Access to default overlay (existing)
- No studio access

### PRO Tier ($X/month)
- Full Studio access
- 10 custom overlays
- All templates
- Basic analytics

### PRO+ Tier ($Y/month)
- Unlimited overlays
- Custom templates (upload own)
- Advanced animations
- Sound effect library
- Priority support

### Beta Access
- PRO users get early access
- Beta badge on studio
- Feedback mechanism
- Reduced price during beta

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up `/studio` route and layout
- [ ] Integrate Fabric.js or React-Draggable
- [ ] Build widget library sidebar
- [ ] Build properties panel
- [ ] Basic drag-drop functionality

### Phase 2: Templates (Week 3)
- [ ] Design 6 launch templates
- [ ] Template gallery page
- [ ] Template → Editor flow
- [ ] Template preview images

### Phase 3: Data Integration (Week 4)
- [ ] Connect Xbox API to widgets
- [ ] Real-time data updates
- [ ] Achievement webhook handling
- [ ] Data binding UI

### Phase 4: Preview & Deploy (Week 5)
- [ ] Live preview in editor
- [ ] Generate OBS URL
- [ ] Server-side rendering
- [ ] WebSocket real-time updates

### Phase 5: Polish (Week 6)
- [ ] Animations library
- [ ] Sound effects
- [ ] Undo/redo system
- [ ] Mobile responsive studio

### Phase 6: Launch (Week 7)
- [ ] Beta testing with PRO users
- [ ] Analytics dashboard
- [ ] Documentation
- [ ] Tutorial videos

---

## File Structure

```
streamtracker-web/
├── src/
│   ├── components/
│   │   └── studio/
│   │       ├── Canvas.jsx
│   │       ├── WidgetLibrary.jsx
│   │       ├── PropertiesPanel.jsx
│   │       ├── Toolbar.jsx
│   │       ├── TemplateGallery.jsx
│   │       ├── PreviewModal.jsx
│   │       └── widgets/
│   │           ├── XboxWidgets.jsx
│   │           ├── BasicElements.jsx
│   │           └── index.js
│   ├── pages/
│   │   └── Studio/
│   │       ├── index.jsx
│   │       ├── Editor.jsx
│   │       └── Templates.jsx
│   ├── hooks/
│   │   ├── useStudio.js
│   │   ├── useDragDrop.js
│   │   └── useOverlayData.js
│   ├── store/
│   │   └── studioStore.js
│   └── utils/
│       └── studio/
│           ├── animations.js
│           ├── templates.js
│           └── dataBindings.js
├── server/
│   └── routes/
│       └── studio.js
└── public/
    └── templates/
        ├── achievement-hunter.jpg
        ├── speedrun-tracker.jpg
        └── ...
```

---

## Success Metrics

- **Adoption:** % of PRO users creating custom overlays
- **Engagement:** Avg time spent in studio
- **Retention:** Studio users vs non-studio PRO users
- **Revenue:** Upgrade rate from PRO to PRO+
- **Feedback:** NPS score from beta users

---

## Notes for Codex

1. **Keep existing overlay as DEFAULT** - Don't break current users
2. **Feature flag** - Use `studio_enabled` flag for gradual rollout
3. **Performance** - Canvas must stay 60fps with multiple animated elements
4. **Accessibility** - Keyboard navigation for editor (tab, arrows, delete)
5. **Export format** - JSON configuration that can be version controlled

---

## References

- **Inspiration:** https://streamcopilot.app/
- **Similar:** StreamElements overlay editor, OBS Studio
- **Differentiator:** Xbox/achievement data integration

---

**Created:** 2026-03-10
**Status:** Ready for Implementation
**Priority:** HIGH - Major PRO feature
