from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os

import sys
sys.path.append('/opt/streamtracker/backend')

from database import SessionLocal, User, ApiKey, GlobalGameName
from auth.steam import get_current_user
from services.steam_api import get_active_steam_game, fetch_achievements

overlay_router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_api_key(api_key: str, db: Session):
    """Verify API key and return user"""
    key_record = db.query(ApiKey).filter(ApiKey.key == api_key, ApiKey.is_active == True).first()
    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    key_record.last_used = datetime.utcnow()
    db.commit()
    
    return key_record.user

@overlay_router.get("/{username}", response_class=HTMLResponse)
def get_overlay(username: str, key: str, theme: str = "fire", db: Session = Depends(get_db)):
    """Serve overlay HTML"""
    user = verify_api_key(key, db)
    
    # Check if user has Steam credentials
    if not user.steam_api_key or not user.steam_id:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html><body style="color:white;background:#333;font-family:Arial;padding:20px;">
            <h3>⚠️ Steam Credentials Required</h3>
            <p>Please add your Steam API key and Steam ID in the dashboard.</p>
        </body></html>
        """)
    
    # Theme colors
    themes = {
        "fire": "#e3350d",
        "water": "#0d47e3", 
        "grass": "#0de335",
        "electric": "#e3d50d",
        "dark": "#333333",
        "gold": "#ffd700"
    }
    
    # Free users only get fire theme
    if not user.is_premium:
        theme = "fire"
    
    theme_color = themes.get(theme, themes["fire"])
    
    # Show watermark for free users
    watermark = ""
    if not user.is_premium:
        watermark = '<div style="position:absolute;bottom:5px;right:5px;font-size:10px;opacity:0.5;">StreamTracker</div>'
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>StreamTracker Overlay</title>
    <style>
        body {{ margin: 0; font-family: 'Segoe UI', Arial, sans-serif; background: transparent; color: white; overflow: hidden; }}
        .overlay {{ 
            background: linear-gradient(135deg, rgba(0,0,0,0.9) 0%, rgba(30,30,30,0.95) 100%);
            border-radius: 12px;
            padding: 20px;
            display: inline-block;
            min-width: 300px;
            border-left: 4px solid {theme_color};
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}
        .game-name {{ font-weight: bold; font-size: 20px; margin-bottom: 10px; color: {theme_color}; }}
        .edit-icon {{ 
            font-size: 12px; 
            cursor: pointer; 
            margin-left: 8px; 
            opacity: 0.7;
        }}
        .edit-icon:hover {{ opacity: 1; }}
        .custom-badge {{
            font-size: 10px;
            background: {theme_color};
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            margin-left: 8px;
            vertical-align: middle;
        }}
        .progress-bar {{ 
            background: rgba(255,255,255,0.2); 
            border-radius: 10px; 
            height: 20px; 
            margin: 10px 0;
            overflow: hidden;
        }}
        .progress-fill {{ 
            background: {theme_color}; 
            height: 100%; 
            border-radius: 10px;
            transition: width 0.5s ease;
        }}
        .stats {{ font-size: 14px; color: #ccc; }}
        .recent {{ margin-top: 15px; }}
        .achievement {{ 
            display: flex; 
            align-items: center; 
            margin: 8px 0;
            font-size: 13px;
        }}
        .achievement img {{ width: 32px; height: 32px; margin-right: 10px; border-radius: 4px; }}
        {watermark}
    </style>
</head>
<body>
    <div class="overlay">
        <div class="game-name">
            <span id="game">Loading...</span>
            <span class="edit-icon" id="edit-btn" style="display:none;" title="Rename game">✏️</span>
            <span class="custom-badge" id="custom-badge" style="display:none;">CUSTOM</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" id="progress-bar" style="width: 0%"></div>
        </div>
        <div class="stats" id="stats">--/-- achievements</div>
        <div class="recent" id="recent"></div>
        {watermark}
    </div>
    
    <script>
        const API_KEY = "{key}";
        const USERNAME = "{username}";
        let currentAppId = null;
        let currentGameName = null;
        let hasCustomName = false;
        
        async function refresh() {{
            try {{
                const resp = await fetch(`/overlay/${{USERNAME}}/data?key=${{API_KEY}}`);
                const data = await resp.json();
                
                currentAppId = data.game_id;
                currentGameName = data.game;
                hasCustomName = data.has_custom_name;
                
                document.getElementById('game').textContent = data.game || 'No game detected';
                document.getElementById('edit-btn').style.display = data.game ? 'inline' : 'none';
                document.getElementById('custom-badge').style.display = data.has_custom_name ? 'inline' : 'none';
                
                document.getElementById('stats').textContent = 
                    `${{data.unlocked || 0}}/${{data.total || 0}} achievements (${{data.completion || 0}}%)`;
                
                const progress = data.total > 0 ? (data.unlocked / data.total * 100) : 0;
                document.getElementById('progress-bar').style.width = `${{progress}}%`;
                
                // Show recent unlocks
                const recentDiv = document.getElementById('recent');
                if (data.recent && data.recent.length > 0) {{
                    recentDiv.innerHTML = '<div style="font-size:12px;color:#999;margin-bottom:5px;">Recent:</div>' +
                        data.recent.map(a => `
                            <div class="achievement">
                                <img src="${{a.icon || ''}}" onerror="this.style.display='none'">
                                <span>${{a.name}}</span>
                            </div>
                        `).join('');
                }} else {{
                    recentDiv.innerHTML = '';
                }}
            }} catch (e) {{
                console.error('Refresh failed:', e);
            }}
        }}
        
        // Edit button click handler
        document.getElementById('edit-btn').addEventListener('click', () => {{
            if (!currentAppId || !currentGameName) return;
            
            const newName = prompt(`Rename "${{currentGameName}}":`, currentGameName);
            if (newName && newName !== currentGameName) {{
                // Note: To actually save, user needs to use dashboard
                // This is just a visual indicator in overlay
                alert(`To permanently save "${{newName}}" as the custom name, use the Rename button in your dashboard.`);
            }}
        }});
        
        refresh();
        setInterval(refresh, 10000);
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)

@overlay_router.get("/{username}/data")
def get_overlay_data(username: str, key: str, db: Session = Depends(get_db)):
    """Return overlay data as JSON - uses user's own Steam API key"""
    user = verify_api_key(key, db)
    
    # Check if user has Steam credentials
    if not user.steam_api_key or not user.steam_id:
        return {
            "user": user.username,
            "game": None,
            "error": "Steam credentials not configured",
            "setup_required": True,
            "is_premium": user.is_premium
        }
    
    # Get currently playing game using USER'S API key
    app_id = get_active_steam_game(user.steam_api_key, user.steam_id)
    
    if not app_id:
        return {
            "user": user.username,
            "game": None,
            "game_id": None,
            "unlocked": 0,
            "total": 0,
            "completion": 0,
            "recent": [],
            "is_premium": user.is_premium
        }
    
    # Fetch achievements using USER'S API key - PASS user_id for name overrides
    data = fetch_achievements(user.steam_api_key, user.steam_id, app_id, user.id)
    
    return {
        "user": user.username,
        "game": data.get('game_name'),
        "game_id": data.get('game_id'),
        "steam_api_name": data.get('steam_api_name'),
        "has_custom_name": data.get('has_custom_name', False),
        "unlocked": data.get('unlocked', 0),
        "total": data.get('total', 0),
        "completion": data.get('completion', 0),
        "recent": data.get('recent', []),
        "is_premium": user.is_premium
    }

@overlay_router.get("/{username}/vertical", response_class=HTMLResponse)
def get_vertical_overlay(username: str, key: str, db: Session = Depends(get_db)):
    """Serve vertical overlay (9:16) - Premium only"""
    user = verify_api_key(key, db)
    
    if not user.is_premium:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html><body style="color:white;background:#333;font-family:Arial;padding:20px;">
            <h3>⭐ Premium Feature</h3>
            <p>Vertical mode requires a premium subscription.</p>
        </body></html>
        """)
    
    return HTMLResponse(content="<h1>Vertical Mode - Coming Soon</h1>")
