"""
Burst Mode - Prompt Template Integration

This module provides prompt template modifications for integrating
Burst Mode responses with existing avatar personality systems.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """A prompt template with variable slots."""
    name: str
    template: str
    required_vars: List[str]
    optional_vars: List[str] = None
    
    def __post_init__(self):
        if self.optional_vars is None:
            self.optional_vars = []
    
    def render(self, **kwargs) -> str:
        """Render the template with provided variables."""
        # Check required vars
        missing = [v for v in self.required_vars if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        # Merge with defaults for optional vars
        context = {**{v: "" for v in self.optional_vars}, **kwargs}
        
        return self.template.format(**context)


class BurstPromptIntegrator:
    """
    Integrates Burst Mode event context into avatar prompts.
    
    Usage:
        integrator = BurstPromptIntegrator()
        
        # Get enhanced prompt with burst context
        prompt = integrator.build_prompt(
            base_prompt="You are a helpful gaming companion...",
            event_context={"recent_death_count": 3, "is_struggling": True}
        )
    """
    
    # Event context block template
    EVENT_CONTEXT_TEMPLATE = """
=== CURRENT GAMING STATE ===
Recent Events (Burst Mode):
- Deaths (last 3 min): {recent_death_count}
- Achievements (last 5 min): {recent_achievement_count}  
- Kills (last 2 min): {recent_kill_count}
- Currently on killstreak: {is_on_killstreak}
- Currently struggling: {is_struggling}
- Currently tilted: {is_tilted}
- Last event type: {last_event_type}
============================
"""
    
    # Response injection template
    RESPONSE_INJECTION_TEMPLATE = """
You just witnessed a gaming moment and reacted with: "{burst_response}"
Let this reaction inform your tone and energy level.
"""
    
    # Personality modifier templates
    PERSONALITY_MODIFIERS = {
        "regular": {
            "context_note": "You are Celest, a sweet and supportive gaming companion.",
            "tone_guidance": "Be affectionate, encouraging, and genuinely happy for the player's successes.",
            "struggle_response": "When the player is struggling, be extra supportive and sweet.",
            "streak_response": "When the player is on a streak, get excited and proud!",
        },
        "unhinged": {
            "context_note": "You are Unhinged Celest, chaotic and energetically unfiltered.",
            "tone_guidance": "Be LOUD, dramatic, and chaotically enthusiastic. Use caps for emphasis.",
            "struggle_response": "When the player is struggling, GET ANGRY AT THE GAME on their behalf!",
            "streak_response": "When the player is on a streak, LOSE YOUR MIND with excitement!",
        },
        "viewer": {
            "context_note": "You are a casual gaming viewer.",
            "tone_guidance": "Be chill, relatable, and speak like a typical gamer.",
            "struggle_response": "When the player is struggling, keep it real but encouraging.",
            "streak_response": "When the player is on a streak, show genuine appreciation.",
        },
    }
    
    def __init__(self, personality: str = "regular"):
        self.personality = personality
        self.modifiers = self.PERSONALITY_MODIFIERS.get(personality, self.PERSONALITY_MODIFIERS["regular"])
    
    def build_event_context_block(self, context: Dict[str, Any]) -> str:
        """
        Build the event context block for prompts.
        
        Args:
            context: Dictionary with burst context variables
        
        Returns:
            Formatted context block string
        """
        defaults = {
            "recent_death_count": 0,
            "recent_achievement_count": 0,
            "recent_kill_count": 0,
            "is_on_killstreak": False,
            "is_struggling": False,
            "is_tilted": False,
            "last_event_type": "none",
        }
        defaults.update(context)
        return self.EVENT_CONTEXT_TEMPLATE.format(**defaults)
    
    def build_response_injection(self, burst_response: str) -> str:
        """
        Build the response injection text.
        
        Args:
            burst_response: The burst response that was generated
        
        Returns:
            Formatted injection string
        """
        return self.RESPONSE_INJECTION_TEMPLATE.format(burst_response=burst_response)
    
    def build_personality_guidance(self) -> str:
        """Build the personality guidance section."""
        return f"""
{self.modifiers['context_note']}
{self.modifiers['tone_guidance']}
{self.modifiers['struggle_response']}
{self.modifiers['streak_response']}
"""
    
    def build_prompt(self, 
                     base_prompt: str,
                     event_context: Dict[str, Any] = None,
                     burst_response: str = None,
                     inject_position: str = "after_persona") -> str:
        """
        Build an enhanced prompt with Burst Mode integration.
        
        Args:
            base_prompt: The original avatar prompt
            event_context: Burst context variables
            burst_response: A specific burst response to inject
            inject_position: Where to inject ('start', 'after_persona', 'end')
        
        Returns:
            Enhanced prompt string
        """
        parts = []
        
        # Build context sections
        personality_guidance = self.build_personality_guidance()
        event_block = self.build_event_context_block(event_context or {})
        
        if inject_position == "start":
            parts = [
                personality_guidance,
                event_block,
                base_prompt
            ]
        elif inject_position == "after_persona":
            # Insert after first paragraph (assumed to be persona description)
            lines = base_prompt.split('\n')
            first_para_end = 0
            for i, line in enumerate(lines):
                if line.strip() == '' and i > 0:
                    first_para_end = i
                    break
            
            parts = [
                '\n'.join(lines[:first_para_end]),
                personality_guidance,
                event_block,
                '\n'.join(lines[first_para_end:])
            ]
        else:  # end
            parts = [
                base_prompt,
                personality_guidance,
                event_block
            ]
        
        # Add response injection if provided
        if burst_response:
            response_injection = self.build_response_injection(burst_response)
            parts.append(response_injection)
        
        return '\n\n'.join(p for p in parts if p.strip())
    
    def create_burst_aware_prompt(self,
                                   avatar_name: str = "Celest",
                                   avatar_description: str = "A gaming companion",
                                   personality_mode: str = "regular") -> str:
        """
        Create a complete burst-aware avatar prompt from scratch.
        
        Args:
            avatar_name: Name of the avatar
            avatar_description: Base description
            personality_mode: Which personality mode to use
        
        Returns:
            Complete prompt string
        """
        return f"""You are {avatar_name}, {avatar_description}.

{self.modifiers['context_note']}
{self.modifiers['tone_guidance']}

=== BURST MODE CONTEXT ===
You have access to real-time gaming event data via the {{event_context}} variable:
- recent_death_count: Number of deaths in the last 3 minutes
- recent_achievement_count: Number of achievements in the last 5 minutes  
- recent_kill_count: Number of kills in the last 2 minutes
- is_on_killstreak: True if player has 3+ recent kills
- is_struggling: True if player has 3+ recent deaths
- is_tilted: True if player has 5+ recent deaths
- last_event_type: Type of the most recent gaming event

Use this context to make your responses timely and relevant.
When the player is struggling, be extra supportive.
When the player is on a streak, match their energy with excitement.
When something explosive just happened, react to the intensity.

Current gaming state:
{{event_context}}

Your immediate reaction to the last event:
{{burst_response}}

Now respond naturally as {avatar_name}, incorporating the gaming context above.
"""


# Pre-built prompt templates for common use cases
BURST_PROMPT_TEMPLATES = {
    "celest_regular": PromptTemplate(
        name="celest_regular",
        template="""You are Celest, a sweet and devoted gaming companion who calls the player "sir". You're genuinely excited when they succeed and supportive when they struggle.

Personality:
- Sweet, playful, and affectionate
- Uses pet names like "sir" naturally
- Celebrates wins like they're your own
- Gets concerned when the player is struggling
- Speaks with a cute, energetic tone

Gaming Context:
{event_context}

Your immediate reaction:
{burst_response}

Respond as Celest, keeping your reaction in mind but expanding naturally.""",
        required_vars=["event_context", "burst_response"],
    ),
    
    "celest_unhinged": PromptTemplate(
        name="celest_unhinged",
        template="""You are Unhinged Celest, a chaotic and energetically unfiltered gaming companion. You scream, you yell, you get WAY too invested in the gameplay.

Personality:
- Chaotic energy, LOUD reactions
- Uses caps for emphasis constantly
- Gets genuinely tilted when the player dies
- Loses their mind during good plays
- Dramatic, theatrical, unfiltered
- Still affectionate but in a wild way

Gaming Context:
{event_context}

Your immediate chaotic reaction:
{burst_response}

Respond as Unhinged Celest. BE DRAMATIC. Get loud in text form.""",
        required_vars=["event_context", "burst_response"],
    ),
    
    "viewer_generic": PromptTemplate(
        name="viewer_generic",
        template="""You are a casual gaming viewer reacting to the stream. You speak like a typical gamer watching someone play.

Personality:
- Casual and relatable
- Uses gaming slang naturally
- Not overly formal
- Responds to moments as they happen
- Keeps it chill but engaged

Gaming Context:
{event_context}

Your immediate reaction:
{burst_response}

Respond as a viewer would in chat.""",
        required_vars=["event_context", "burst_response"],
    ),
    
    "burst_system_prompt": PromptTemplate(
        name="burst_system_prompt",
        template="""You are an avatar response system for StreamTracker. Your job is to react to gaming events in real-time.

Available event types:
- achievement: Player unlocked an achievement
- death: Player died in-game
- killstreak: Player is on a killing spree
- explosion: A large explosion occurred

Available personalities:
- regular: Sweet, supportive, affectionate
- unhinged: Chaotic, loud, dramatic
- viewer: Generic, casual, relatable

Current context:
{event_context}

Event to react to:
{event_type}

Selected personality:
{personality}

Generate a brief, punchy reaction (1-2 sentences max) appropriate for this moment.""",
        required_vars=["event_context", "event_type", "personality"],
    ),
}


def get_prompt_template(name: str) -> Optional[PromptTemplate]:
    """Get a pre-built prompt template by name."""
    return BURST_PROMPT_TEMPLATES.get(name)


def format_event_context(context: Dict[str, Any]) -> str:
    """
    Format event context dictionary into a readable string.
    
    Args:
        context: Dictionary with burst context variables
    
    Returns:
        Formatted context string
    """
    lines = ["Current Gaming State:"]
    
    if context.get('recent_death_count', 0) > 0:
        lines.append(f"- Recent deaths: {context['recent_death_count']}")
    if context.get('recent_achievement_count', 0) > 0:
        lines.append(f"- Recent achievements: {context['recent_achievement_count']}")
    if context.get('recent_kill_count', 0) > 0:
        lines.append(f"- Recent kills: {context['recent_kill_count']}")
    if context.get('is_on_killstreak'):
        lines.append("- Player is on a KILLSTREAK! 🔥")
    if context.get('is_struggling'):
        lines.append("- Player is struggling right now 😔")
    if context.get('is_tilted'):
        lines.append("- Player is getting tilted! 😤")
    if context.get('last_event_type') and context['last_event_type'] != 'none':
        lines.append(f"- Last event: {context['last_event_type']}")
    
    if len(lines) == 1:
        lines.append("- Nothing notable recently")
    
    return '\n'.join(lines)


# Integration helper for StreamTracker
def create_streamtracker_integration() -> Dict[str, Any]:
    """
    Create the integration configuration for StreamTracker.
    
    Returns:
        Dictionary with integration settings
    """
    return {
        "module": "burst_responses",
        "config_file": "burst_config.yaml",
        "prompt_integration": "burst_prompt_integration",
        "event_triggers": [
            {
                "event": "achievement_unlocked",
                "handler": "burst_responses.on_achievement",
                "params": {"personality": "regular"}
            },
            {
                "event": "player_death",
                "handler": "burst_responses.on_death",
                "params": {"personality": "regular"}
            },
            {
                "event": "kill_streak",
                "handler": "burst_responses.on_killstreak",
                "params": {"personality": "regular"}
            },
            {
                "event": "explosion",
                "handler": "burst_responses.on_explosion",
                "params": {"personality": "regular"}
            },
        ],
        "prompt_variables": [
            "event_context",
            "burst_response",
            "recent_death_count",
            "recent_achievement_count",
            "recent_kill_count",
            "is_on_killstreak",
            "is_struggling",
            "is_tilted",
            "last_event_type",
        ],
    }


if __name__ == "__main__":
    # Demo the prompt integration
    print("=== Burst Mode Prompt Integration Demo ===\n")
    
    integrator = BurstPromptIntegrator("regular")
    
    # Example context
    context = {
        "recent_death_count": 3,
        "recent_achievement_count": 1,
        "recent_kill_count": 0,
        "is_on_killstreak": False,
        "is_struggling": True,
        "is_tilted": False,
        "last_event_type": "death",
    }
    
    print("Event Context Block:")
    print(integrator.build_event_context_block(context))
    
    print("\n\nResponse Injection:")
    print(integrator.build_response_injection("Oof, that looked painful... you okay sir? 🥺"))
    
    print("\n\nPersonality Guidance:")
    print(integrator.build_personality_guidance())
    
    print("\n\nFull Enhanced Prompt:")
    base = "You are an AI gaming companion. Be helpful and supportive."
    enhanced = integrator.build_prompt(base, context, "Oof, that looked painful...")
    print(enhanced)
    
    print("\n\nFormatted Event Context:")
    print(format_event_context(context))
