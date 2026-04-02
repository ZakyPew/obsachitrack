# Burst Mode - Avatar Response System

Fast, punchy, contextual avatar reactions for gaming moments in StreamTracker.

## Overview

Burst Mode provides human-like reactions to gaming events with:
- **3 Personality Modes**: Regular (Celest), Unhinged (Chaotic Celest), and Viewer (Generic)
- **4 Event Types**: Achievements, Deaths, Killstreaks, Explosions
- **Context Awareness**: Detects death streaks, kill streaks, and adjusts tone accordingly
- **Response Variety**: 5-10+ variations per event type to prevent repetition

## Files

| File | Description |
|------|-------------|
| `burst_responses.py` | Core response logic and templates |
| `burst_config.yaml` | Configuration and response definitions |
| `burst_prompt_integration.py` | Prompt template integration |
| `burst_examples.py` | Usage examples and demos |

## Quick Start

```python
from burst_responses import get_burst_manager, on_achievement, on_death

# Get the burst manager
manager = get_burst_manager(personality="regular")

# Get a response
response = manager.get_burst_response("achievement", 
    achievement_name="First Blood"
)
print(response['response'])  # "Yooo, let's go! 🎉"

# Or use convenience functions
print(on_death("unhinged"))  # "NAHHH THAT WAS BULLSHIT..."
```

## Personality Modes

### Regular (Celest)
Sweet, supportive, affectionate. Uses pet names like "sir", celebrates wins enthusiastically, gets concerned when player struggles.

**Examples:**
- "Sir is crushing it! So proud! 💕"
- "Yooo, let's go! 🎉"
- "Oof, that looked painful... you okay sir? 🥺"

### Unhinged
Chaotic, energetic, unfiltered. Screams in text form, gets tilted on player's behalf, LOSES THEIR MIND during good plays.

**Examples:**
- "SIR IS ACTUALLY CRACKED?! Inject this into my VEINS! 💉"
- "I'M SCREAMING. ACTUALLY SCREAMING. AHHHH! 😱"
- "NAHHH THAT WAS BULLSHIT AND WE ALL KNOW IT 🚨"

### Viewer
Generic gaming viewer. Casual, relatable, uses gaming slang.

**Examples:**
- "Nice one!"
- "F"
- "GG! Well played."

## Event Types

| Event | Triggers | Context Variables |
|-------|----------|-------------------|
| `achievement` | Achievement unlocked | `achievement_name`, `rarity_percent` |
| `death` | Player died | `death_count`, `cause` |
| `killstreak` | Multiple kills in succession | `streak_count` |
| `explosion` | Large explosion nearby | `survived`, `damage_taken` |

## Context-Aware Features

### Death Streak Detection
After 3 deaths in 3 minutes, responses become "saltier":

```python
# Death #1: "They got you that time..."
# Death #2: "Oof, that looked painful..."
# Death #3+: "THAT'S 3 DEATHS! I'M ACTUALLY GONNA FIGHT THIS GAME! 👊"
```

### Context Summary
Get a full context summary for prompts:

```python
context = manager.get_context_summary()
# {
#     "recent_death_count": 3,
#     "recent_achievement_count": 1,
#     "recent_kill_count": 0,
#     "is_on_killstreak": False,
#     "is_struggling": True,
#     "is_tilted": False,
#     "last_event_type": "death"
# }
```

## Prompt Integration

Integrate burst responses into avatar prompts:

```python
from burst_prompt_integration import BurstPromptIntegrator, format_event_context

# Create integrator
integrator = BurstPromptIntegrator("regular")

# Build enhanced prompt
enhanced = integrator.build_prompt(
    base_prompt="You are Celest, a gaming companion...",
    event_context=context,
    burst_response="ON FIRE! 🔥"
)
```

Output includes:
- Personality guidance
- Event context block
- Response injection

## StreamTracker Integration

```python
# In app.py or websocket handler
from burst_responses import get_burst_manager, EventType
from websocket_server import push_burst_response

burst_manager = get_burst_manager("regular", "data/burst_history.json")

# When achievement unlocked
def handle_achievement(ach_data):
    response = burst_manager.get_burst_response("achievement",
        achievement_name=ach_data['name'],
        rarity_percent=ach_data.get('rarity', 100)
    )
    
    # Push to overlay/chat
    push_burst_response({
        "type": "burst",
        "event": "achievement",
        "message": response['response'],
        "context": response['context']
    })
```

## Configuration

Edit `burst_config.yaml` to customize:
- Response templates
- Personality definitions
- Event trigger settings
- Context thresholds
- Output formatting

## API Reference

### BurstResponseManager

```python
manager = BurstResponseManager(
    personality=PersonalityMode.REGULAR,
    history_file="path/to/history.json"  # Optional
)

# Get response
response = manager.get_response(EventType.ACHIEVEMENT, context_vars)

# Get full burst response
result = manager.get_burst_response("achievement", **context)
# Returns: {"response": "...", "event_type": "...", "context": {...}}

# Get context
context = manager.get_context_summary()

# Change personality
manager.set_personality(PersonalityMode.UNHINGED)

# Clear history
manager.clear_history()
```

### Convenience Functions

```python
from burst_responses import (
    on_achievement,  # (personality, **context) -> str
    on_death,        # (personality, **context) -> str
    on_killstreak,   # (streak_count, personality, **context) -> str
    on_explosion,    # (personality, **context) -> str
)
```

## Testing

Run the demo:

```bash
cd ~/projects/active/streamtracker-web
python3 burst_responses.py        # Core response demo
python3 burst_prompt_integration.py  # Prompt integration demo
python3 burst_examples.py          # Full examples
```

## Response Examples by Event

### Achievement
- "Yooo, let's go! 🎉"
- "Sir is crushing it! So proud! 💕"
- "POP OFF! 🎊"
- "*cheering noises* YAAASSS! 📣"

### Death
- "F in the chat... 😔"
- "They got you that time, but you'll get them back! 💪"
- "Reset, refocus, destroy. You got this! 🔥"
- (After 3 deaths): "Okay, that's 3 deaths now... you good sir? 😅"

### Killstreak
- "ON FIRE! 🔥"
- "{streak_count} in a row?! Who IS this player?! 🌟"
- "The enemies are shaking right now~ 😈"

### Explosion
- "Holy shit! 💥"
- "That was close! You okay?! 😰"
- "Boom goes the dynamite! 🧨"

## License

Part of StreamTracker - Gaming achievement tracking and streaming tools.
