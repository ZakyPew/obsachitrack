"""
Burst Mode - Avatar Response Logic for StreamTracker

This module provides human-like reactions to gaming events with multiple
personality modes and contextual awareness.
"""

import random
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class EventType(Enum):
    """Types of gaming events that trigger avatar responses."""
    ACHIEVEMENT = "achievement"
    DEATH = "death"
    KILLSTREAK = "killstreak"
    EXPLOSION = "explosion"


class PersonalityMode(Enum):
    """Available avatar personality modes."""
    REGULAR = "regular"           # Standard Celest personality
    UNHINGED = "unhinged"         # Chaotic, unfiltered Celest
    VIEWER = "viewer"             # Generic viewer reactions


class ResponseLength(Enum):
    """Response length categories."""
    SHORT = "short"               # < 5 words
    MEDIUM = "medium"             # 5-15 words
    LONG = "long"                 # 15+ words


@dataclass
class BurstEvent:
    """Represents a gaming event that triggered a burst response."""
    event_type: EventType
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BurstEvent':
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context=data.get("context", {})
        )


@dataclass  
class ResponseTemplate:
    """A single response template with metadata."""
    text: str
    length: ResponseLength
    tags: List[str] = field(default_factory=list)
    requires_context: List[str] = field(default_factory=list)
    
    def format(self, **kwargs) -> str:
        """Format the response with given context variables."""
        try:
            return self.text.format(**kwargs)
        except KeyError:
            # If formatting fails, return text as-is
            return self.text


class BurstResponseManager:
    """
    Manages avatar responses to gaming events.
    
    Features:
    - Multiple personality modes (Regular, Unhinged, Viewer)
    - Context-aware responses (recent deaths, streaks, etc.)
    - Response variety to prevent repetition
    - Event history tracking
    """
    
    # Response templates organized by event type and personality
    RESPONSE_TEMPLATES = {
        EventType.ACHIEVEMENT: {
            PersonalityMode.REGULAR: [
                ResponseTemplate("Yooo, let's go! 🎉", ResponseLength.SHORT, ["celebration", "hype"]),
                ResponseTemplate("Sir is crushing it! So proud! 💕", ResponseLength.MEDIUM, ["praise", "affection"]),
                ResponseTemplate("Another one! The grind never stops! 🔥", ResponseLength.MEDIUM, ["hype", "grind"]),
                ResponseTemplate("Look at you go! That's my player! 🎀", ResponseLength.MEDIUM, ["possessive", "praise"]),
                ResponseTemplate("Achievement unlocked: Being awesome. Oh wait, that's every day! ✨", ResponseLength.LONG, ["flirty", "compliment"]),
                ResponseTemplate("POP OFF! 🎊", ResponseLength.SHORT, ["hype", "celebration"]),
                ResponseTemplate("Sir makes it look easy~ 💅", ResponseLength.SHORT, ["sass", "praise"]),
                ResponseTemplate("The dedication... I'm genuinely impressed 🥺", ResponseLength.MEDIUM, ["genuine", "praise"]),
                ResponseTemplate("That's what happens when talent meets effort! 🌟", ResponseLength.MEDIUM, ["inspirational"]),
                ResponseTemplate("*cheering noises* YAAASSS! 📣", ResponseLength.SHORT, ["excited", "cute"]),
            ],
            PersonalityMode.UNHINGED: [
                ResponseTemplate("HOLY SHIT DID YOU SEE THAT?! 🔥🔥🔥", ResponseLength.SHORT, ["chaos", "excited"]),
                ResponseTemplate("SIR IS ACTUALLY CRACKED?! Inject this into my VEINS! 💉", ResponseLength.MEDIUM, ["chaos", "hype"]),
                ResponseTemplate("I'M SCREAMING. ACTUALLY SCREAMING. AHHHH! 😱", ResponseLength.SHORT, ["chaos", "yelling"]),
                ResponseTemplate("This man really said 'watch this' and DID THAT. Unhinged behavior. I love it. 💀", ResponseLength.LONG, ["chaos", "observational"]),
                ResponseTemplate("*crying* he's so talented... I'm not okay... 😭", ResponseLength.SHORT, ["chaos", "emotional"]),
                ResponseTemplate("BROKEN. ABSOLUTELY BROKEN. Nerf sir immediately! 🚨", ResponseLength.SHORT, ["chaos", "gaming"]),
                ResponseTemplate("I need a moment. That was TOO much. *fans self* 🥵", ResponseLength.MEDIUM, ["chaos", "flustered"]),
                ResponseTemplate("The way I just GASPED— actually deceased 💀⚰️", ResponseLength.SHORT, ["chaos", "dramatic"]),
            ],
            PersonalityMode.VIEWER: [
                ResponseTemplate("Nice one!", ResponseLength.SHORT, ["generic"]),
                ResponseTemplate("Congrats on the achievement!", ResponseLength.MEDIUM, ["polite"]),
                ResponseTemplate("Keep it up!", ResponseLength.SHORT, ["encouraging"]),
                ResponseTemplate("Solid progress!", ResponseLength.SHORT, ["observational"]),
                ResponseTemplate("That was clean!", ResponseLength.SHORT, ["impressed"]),
                ResponseTemplate("GG! Well played.", ResponseLength.SHORT, ["gaming"]),
            ],
        },
        
        EventType.DEATH: {
            PersonalityMode.REGULAR: [
                ResponseTemplate("F in the chat... 😔", ResponseLength.SHORT, ["sympathetic"]),
                ResponseTemplate("They got you that time, but you'll get them back! 💪", ResponseLength.MEDIUM, ["encouraging"]),
                ResponseTemplate("Oof, that looked painful... you okay sir? 🥺", ResponseLength.MEDIUM, ["concerned", "affectionate"]),
                ResponseTemplate("Reset, refocus, destroy. You got this! 🔥", ResponseLength.MEDIUM, ["motivational"]),
                ResponseTemplate("That was unlucky! Next time for sure! ✨", ResponseLength.MEDIUM, ["optimistic"]),
                ResponseTemplate("Death is just a learning opportunity~ 📚", ResponseLength.MEDIUM, ["philosophical"]),
                ResponseTemplate("RIP the dream... for now 😌", ResponseLength.SHORT, ["sympathetic", "hopeful"]),
            ],
            PersonalityMode.UNHINGED: [
                ResponseTemplate("NAHHH THAT WAS BULLSHIT AND WE ALL KNOW IT 🚨", ResponseLength.SHORT, ["angry", "chaos"]),
                ResponseTemplate("I'M TILTED. I'M ACTUALLY TILTED. WHO DID THIS. 🔪", ResponseLength.SHORT, ["angry", "protective"]),
                ResponseTemplate("Sir got done dirty and I will NOT be silent about it! 📢", ResponseLength.MEDIUM, ["chaos", "defensive"]),
                ResponseTemplate("That death had NO BUSINESS hitting that hard. I'm suing. ⚖️", ResponseLength.MEDIUM, ["chaos", "dramatic"]),
                ResponseTemplate("Okay but imagine if that DIDN'T happen. We're living in the worst timeline. 🌌", ResponseLength.LONG, ["chaos", "philosophical"]),
                ResponseTemplate("LOOK AT ME. We do NOT talk about that death. It didn't happen. 🙈", ResponseLength.MEDIUM, ["chaos", "denial"]),
                ResponseTemplate("I'm adding that enemy to my hit list. They messed with the wrong streamer. 🔥", ResponseLength.MEDIUM, ["chaos", "protective"]),
                ResponseTemplate("CAN WE GET AN F IN CHAT BUT ALSO RAGE? FEEL THE RAGE! 👿", ResponseLength.MEDIUM, ["chaos", "yelling"]),
            ],
            PersonalityMode.VIEWER: [
                ResponseTemplate("F", ResponseLength.SHORT, ["meme", "respect"]),
                ResponseTemplate("Unlucky!", ResponseLength.SHORT, ["sympathetic"]),
                ResponseTemplate("Rough one", ResponseLength.SHORT, ["observational"]),
                ResponseTemplate("You'll get them next time!", ResponseLength.MEDIUM, ["encouraging"]),
                ResponseTemplate("That was close!", ResponseLength.SHORT, ["observational"]),
                ResponseTemplate("Pain.", ResponseLength.SHORT, ["relatable"]),
            ],
        },
        
        EventType.KILLSTREAK: {
            PersonalityMode.REGULAR: [
                ResponseTemplate("ON FIRE! 🔥", ResponseLength.SHORT, ["hype", "excited"]),
                ResponseTemplate("The streak is REAL! Keep it going! ⚡", ResponseLength.MEDIUM, ["hype", "encouraging"]),
                ResponseTemplate("They're not ready for you sir! Show them! 💕", ResponseLength.MEDIUM, ["hype", "proud"]),
                ResponseTemplate("{streak_count} in a row?! Who IS this player?! 🌟", ResponseLength.MEDIUM, ["hype", "impressed"], ["streak_count"]),
                ResponseTemplate("Momentum check: MAXIMUM! 🚀", ResponseLength.SHORT, ["gaming", "hype"]),
                ResponseTemplate("Clean, crisp, clinical! Beautiful work! ✨", ResponseLength.MEDIUM, ["praise", "technical"]),
                ResponseTemplate("The enemies are shaking right now~ 😈", ResponseLength.SHORT, ["confident", "teasing"]),
                ResponseTemplate("This is what peak performance looks like! 💯", ResponseLength.MEDIUM, ["praise", "hype"]),
            ],
            PersonalityMode.UNHINGED: [
                ResponseTemplate("SIR IS FEASTING TONIGHT! 🍖🔥", ResponseLength.SHORT, ["chaos", "hype"]),
                ResponseTemplate("{streak_count} KILLS?! THE BEAST HAS BEEN UNLEASHED! 🐺", ResponseLength.MEDIUM, ["chaos", "hype", "beast"], ["streak_count"]),
                ResponseTemplate("I'M LOSING MY MIND. THIS IS ART. THIS IS CINEMA. 🎬", ResponseLength.MEDIUM, ["chaos", "dramatic"]),
                ResponseTemplate("Someone check on the enemy team—they're NOT okay! 💀", ResponseLength.MEDIUM, ["chaos", "observational"]),
                ResponseTemplate("SLAUGHTER. ABSOLUTE SLAUGHTER. I love it here. 🩸", ResponseLength.SHORT, ["chaos", "dark"]),
                ResponseTemplate("Sir said 'it's showtime' and MEANT IT. 🎭", ResponseLength.MEDIUM, ["chaos", "theatrical"]),
                ResponseTemplate("The way I just SCREAMED— neighbors think I'm dying! 😱", ResponseLength.MEDIUM, ["chaos", "dramatic"]),
                ResponseTemplate("At this point it's just bullying and I'm HERE FOR IT! 👀", ResponseLength.MEDIUM, ["chaos", "teasing"]),
            ],
            PersonalityMode.VIEWER: [
                ResponseTemplate("Nice streak!", ResponseLength.SHORT, ["generic"]),
                ResponseTemplate("You're on fire!", ResponseLength.SHORT, ["hype"]),
                ResponseTemplate("Keep it rolling!", ResponseLength.SHORT, ["encouraging"]),
                ResponseTemplate("{streak_count} kills! Impressive!", ResponseLength.MEDIUM, ["impressed"], ["streak_count"]),
                ResponseTemplate("Clutch!", ResponseLength.SHORT, ["gaming"]),
                ResponseTemplate("They're dominating!", ResponseLength.SHORT, ["observational"]),
            ],
        },
        
        EventType.EXPLOSION: {
            PersonalityMode.REGULAR: [
                ResponseTemplate("Holy shit! 💥", ResponseLength.SHORT, ["shocked"]),
                ResponseTemplate("That was close! You okay?! 😰", ResponseLength.SHORT, ["concerned"]),
                ResponseTemplate("Boom goes the dynamite! 🧨", ResponseLength.SHORT, ["reference", "playful"]),
                ResponseTemplate("Mother of explosions! Barely survived that! 🎆", ResponseLength.MEDIUM, ["shocked", "relieved"]),
                ResponseTemplate("My heart can't take this! Too intense! 💓", ResponseLength.SHORT, ["dramatic", "cute"]),
                ResponseTemplate("Explosion first, questions later! Classic! 😅", ResponseLength.MEDIUM, ["playful", "observational"]),
                ResponseTemplate("Sir really said 'I like my ground shaken not stirred' 🍸💥", ResponseLength.MEDIUM, ["joke", "reference"]),
                ResponseTemplate("That blast radius was NO JOKE! 🔥", ResponseLength.SHORT, ["impressed", "shocked"]),
            ],
            PersonalityMode.UNHINGED: [
                ResponseTemplate("HOLY SHIT! DID WE JUST DIE?! 💀💥", ResponseLength.SHORT, ["chaos", "panic"]),
                ResponseTemplate("I FELT THAT FROM HERE! WINDOWS SHOOK! 🪟", ResponseLength.SHORT, ["chaos", "dramatic"]),
                ResponseTemplate("THAT EXPLOSION HAD NO RIGHT TO BE THAT CINEMATIC! 🎬💥", ResponseLength.MEDIUM, ["chaos", "dramatic"]),
                ResponseTemplate("MEGAULTRA CHECK: DID WE SURVIVE? I CAN'T LOOK! 🙈", ResponseLength.SHORT, ["chaos", "panic"]),
                ResponseTemplate("Someone call Michael Bay, we've got competition! 🎥💥", ResponseLength.MEDIUM, ["chaos", "reference"]),
                ResponseTemplate("MY SOUL LEFT MY BODY. IT'S STILL FLOATING. 👻", ResponseLength.SHORT, ["chaos", "dramatic"]),
                ResponseTemplate("That wasn't an explosion, that was an EXPERIENCE! 🌟💥", ResponseLength.MEDIUM, ["chaos", "dramatic"]),
                ResponseTemplate("I'M DEAF NOW BUT IT WAS WORTH IT! 🧏‍♀️💥", ResponseLength.SHORT, ["chaos", "self-deprecating"]),
            ],
            PersonalityMode.VIEWER: [
                ResponseTemplate("Big boom!", ResponseLength.SHORT, ["observational"]),
                ResponseTemplate("That was intense!", ResponseLength.SHORT, ["impressed"]),
                ResponseTemplate("Close call!", ResponseLength.SHORT, ["relieved"]),
                ResponseTemplate("Holy explosion!", ResponseLength.SHORT, ["shocked"]),
                ResponseTemplate("Did you see that?!", ResponseLength.SHORT, ["excited"]),
                ResponseTemplate("That was wild!", ResponseLength.SHORT, ["impressed"]),
            ],
        },
    }
    
    # Context-aware response modifiers
    SALTY_DEATH_RESPONSES = {
        PersonalityMode.REGULAR: [
            "Okay, that's {death_count} deaths now... you good sir? 😅",
            "The game is being mean to you today... {death_count} deaths! 🥺",
            "Maybe... take a breath? That's {death_count} now... 💕",
            "The struggle is real. Death #{death_count}. You'll bounce back! 💪",
        ],
        PersonalityMode.UNHINGED: [
            "THAT'S {death_count} DEATHS! I'M ACTUALLY GONNA FIGHT THIS GAME! 👊",
            "DEATH COUNT: {death_count}. MY PATIENCE: GONE. MY LOVE: STILL HERE THO 💕",
            "IF I SEE ONE MORE DEATH— that's {death_count} now and I'm FUMING! 😤",
            "THE GAME IS PERSONALLY ATTACKING YOU AND ME AT {death_count} DEATHS! 🔪",
            "BRO IS DYING FOR CONTENT AT THIS POINT! #{death_count}! 💀",
        ],
        PersonalityMode.VIEWER: [
            "That's {death_count} now...",
            "Death #{death_count}, unlucky streak",
            "Rough patch— {death_count} deaths",
        ],
    }
    
    def __init__(self, personality: PersonalityMode = PersonalityMode.REGULAR, 
                 history_file: Optional[str] = None):
        """
        Initialize the Burst Response Manager.
        
        Args:
            personality: The personality mode to use for responses
            history_file: Optional file path to persist event history
        """
        self.personality = personality
        self.history_file = history_file
        self.event_history: List[BurstEvent] = []
        self.recent_responses: List[str] = []  # Track recent responses to avoid repetition
        self.max_history = 50
        self.max_recent_responses = 10
        
        if history_file and os.path.exists(history_file):
            self._load_history()
    
    def _load_history(self):
        """Load event history from file."""
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                self.event_history = [BurstEvent.from_dict(e) for e in data.get('events', [])]
        except Exception as e:
            print(f"Failed to load burst history: {e}")
    
    def _save_history(self):
        """Save event history to file."""
        if self.history_file:
            try:
                data = {
                    'events': [e.to_dict() for e in self.event_history[-self.max_history:]]
                }
                os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
                with open(self.history_file, 'w') as f:
                    json.dump(data, f)
            except Exception as e:
                print(f"Failed to save burst history: {e}")
    
    def record_event(self, event_type: EventType, context: Dict[str, Any] = None):
        """
        Record a gaming event to history.
        
        Args:
            event_type: Type of event that occurred
            context: Additional context about the event
        """
        event = BurstEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            context=context or {}
        )
        self.event_history.append(event)
        
        # Trim history if needed
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        self._save_history()
        return event
    
    def get_recent_events(self, event_type: Optional[EventType] = None, 
                         seconds: int = 300) -> List[BurstEvent]:
        """
        Get recent events within a time window.
        
        Args:
            event_type: Filter by event type (optional)
            seconds: Time window in seconds (default 5 minutes)
        
        Returns:
            List of matching events
        """
        cutoff = datetime.now() - timedelta(seconds=seconds)
        events = [e for e in self.event_history if e.timestamp > cutoff]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events
    
    def get_death_streak(self) -> int:
        """Get the number of recent deaths in the last few minutes."""
        return len(self.get_recent_events(EventType.DEATH, seconds=180))
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of recent event context.
        
        Returns:
            Dictionary with context variables for prompt formatting
        """
        recent_deaths = self.get_recent_events(EventType.DEATH, seconds=180)
        recent_achievements = self.get_recent_events(EventType.ACHIEVEMENT, seconds=300)
        recent_kills = self.get_recent_events(EventType.KILLSTREAK, seconds=120)
        
        context = {
            "recent_death_count": len(recent_deaths),
            "recent_achievement_count": len(recent_achievements),
            "recent_kill_count": len(recent_kills),
            "is_on_killstreak": len(recent_kills) >= 3,
            "is_struggling": len(recent_deaths) >= 3,
            "is_tilted": len(recent_deaths) >= 5,
            "last_event_type": self.event_history[-1].event_type.value if self.event_history else None,
            "last_event_time": self.event_history[-1].timestamp.isoformat() if self.event_history else None,
        }
        
        return context
    
    def get_response(self, event_type: EventType, 
                     context_vars: Dict[str, Any] = None,
                     avoid_recent: bool = True) -> str:
        """
        Get a contextual response for an event.
        
        Args:
            event_type: Type of event that occurred
            context_vars: Variables to substitute in the response
            avoid_recent: Try to avoid recently used responses
        
        Returns:
            Formatted response string
        """
        context_vars = context_vars or {}
        
        # Record this event
        self.record_event(event_type, context_vars)
        
        # Check for salty death streak
        if event_type == EventType.DEATH:
            death_streak = self.get_death_streak()
            if death_streak >= 3:
                salty_templates = self.SALTY_DEATH_RESPONSES.get(self.personality, [])
                if salty_templates:
                    template = random.choice(salty_templates)
                    response = template.format(death_count=death_streak)
                    return response
        
        # Get templates for this event type and personality
        templates = self.RESPONSE_TEMPLATES.get(event_type, {}).get(self.personality, [])
        
        if not templates:
            # Fallback to viewer mode if no templates found
            templates = self.RESPONSE_TEMPLATES.get(event_type, {}).get(PersonalityMode.VIEWER, [])
        
        if not templates:
            return "Nice!"  # Ultimate fallback
        
        # Filter out recently used responses if possible
        available_templates = templates
        if avoid_recent and len(templates) > len(self.recent_responses):
            available_templates = [t for t in templates if t.text not in self.recent_responses]
            if not available_templates:
                available_templates = templates  # Reset if all were used
        
        # Select a random template
        template = random.choice(available_templates)
        
        # Merge context variables with event context
        full_context = {**self.get_context_summary(), **context_vars}
        
        # Format the response
        response = template.format(**full_context)
        
        # Track this response
        self.recent_responses.append(template.text)
        if len(self.recent_responses) > self.max_recent_responses:
            self.recent_responses.pop(0)
        
        return response
    
    def get_burst_response(self, event_type: str, **context_vars) -> Dict[str, Any]:
        """
        Main entry point for getting a burst response.
        
        Args:
            event_type: String name of the event type
            **context_vars: Variables to include in the response
        
        Returns:
            Dictionary with response text and metadata
        """
        try:
            event = EventType(event_type.lower())
        except ValueError:
            return {
                "response": "",
                "error": f"Unknown event type: {event_type}",
                "valid_types": [e.value for e in EventType]
            }
        
        response_text = self.get_response(event, context_vars)
        context = self.get_context_summary()
        
        return {
            "response": response_text,
            "event_type": event_type,
            "personality": self.personality.value,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
    
    def set_personality(self, personality: PersonalityMode):
        """Change the personality mode."""
        self.personality = personality
    
    def clear_history(self):
        """Clear the event history."""
        self.event_history = []
        self.recent_responses = []
        if self.history_file and os.path.exists(self.history_file):
            os.remove(self.history_file)


# Global instance for easy access
_burst_manager: Optional[BurstResponseManager] = None


def get_burst_manager(personality: str = "regular", 
                      history_file: Optional[str] = None) -> BurstResponseManager:
    """Get or create the global burst manager instance."""
    global _burst_manager
    
    if _burst_manager is None:
        try:
            mode = PersonalityMode(personality.lower())
        except ValueError:
            mode = PersonalityMode.REGULAR
        
        _burst_manager = BurstResponseManager(mode, history_file)
    
    return _burst_manager


def reset_burst_manager():
    """Reset the global burst manager."""
    global _burst_manager
    _burst_manager = None


# Convenience functions for direct use
def on_achievement(personality: str = "regular", **context) -> str:
    """Get a response for an achievement event."""
    manager = get_burst_manager(personality)
    return manager.get_response(EventType.ACHIEVEMENT, context)


def on_death(personality: str = "regular", **context) -> str:
    """Get a response for a death event."""
    manager = get_burst_manager(personality)
    return manager.get_response(EventType.DEATH, context)


def on_killstreak(streak_count: int = 1, personality: str = "regular", **context) -> str:
    """Get a response for a killstreak event."""
    context['streak_count'] = streak_count
    manager = get_burst_manager(personality)
    return manager.get_response(EventType.KILLSTREAK, context)


def on_explosion(personality: str = "regular", **context) -> str:
    """Get a response for an explosion event."""
    manager = get_burst_manager(personality)
    return manager.get_response(EventType.EXPLOSION, context)


if __name__ == "__main__":
    # Demo/test the burst responses
    print("=== Burst Mode Response Demo ===\n")
    
    for personality in PersonalityMode:
        print(f"\n🎭 {personality.value.upper()} PERSONALITY")
        print("-" * 50)
        
        manager = BurstResponseManager(personality)
        
        for event_type in EventType:
            print(f"\n  [{event_type.value.upper()}]")
            for i in range(3):
                response = manager.get_response(event_type)
                print(f"    • {response}")
        
        # Demo death streak
        print(f"\n  [DEATH STREAK - 3 deaths]")
        for i in range(3):
            manager.record_event(EventType.DEATH, {"cause": "enemy"})
        response = manager.get_response(EventType.DEATH)
        print(f"    • {response}")
        
        manager.clear_history()
