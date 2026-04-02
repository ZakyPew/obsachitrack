"""
Burst Mode - Usage Examples

This file demonstrates how to integrate Burst Mode into StreamTracker.
"""

import json
from burst_responses import (
    BurstResponseManager, EventType, PersonalityMode,
    on_achievement, on_death, on_killstreak, on_explosion,
    get_burst_manager
)
from burst_prompt_integration import (
    BurstPromptIntegrator, format_event_context, get_prompt_template
)


def example_1_basic_usage():
    """Example 1: Basic usage of burst responses."""
    print("=" * 60)
    print("Example 1: Basic Burst Responses")
    print("=" * 60)
    
    # Create a manager with regular personality
    manager = BurstResponseManager(PersonalityMode.REGULAR)
    
    # Simulate various gaming events
    events = [
        (EventType.ACHIEVEMENT, {"achievement_name": "First Blood"}),
        (EventType.DEATH, {"cause": "falling"}),
        (EventType.KILLSTREAK, {"streak_count": 5}),
        (EventType.EXPLOSION, {"survived": True}),
    ]
    
    for event_type, context in events:
        response = manager.get_response(event_type, context)
        print(f"\n[{event_type.value.upper()}]")
        print(f"  Response: {response}")


def example_2_personality_modes():
    """Example 2: Comparing different personality modes."""
    print("\n" + "=" * 60)
    print("Example 2: Personality Mode Comparison")
    print("=" * 60)
    
    event_type = EventType.ACHIEVEMENT
    context = {"achievement_name": "Speedrunner"}
    
    for personality in PersonalityMode:
        manager = BurstResponseManager(personality)
        response = manager.get_response(event_type, context)
        print(f"\n[{personality.value.upper()}]")
        print(f"  {response}")


def example_3_death_streak():
    """Example 3: Context-aware death streak responses."""
    print("\n" + "=" * 60)
    print("Example 3: Death Streak (Context-Aware)")
    print("=" * 60)
    
    manager = BurstResponseManager(PersonalityMode.UNHINGED)
    
    # Simulate multiple deaths
    for i in range(5):
        response = manager.get_response(EventType.DEATH, {"cause": "enemy"})
        print(f"\nDeath #{i+1}:")
        print(f"  {response}")


def example_4_prompt_integration():
    """Example 4: Integrating with avatar prompts."""
    print("\n" + "=" * 60)
    print("Example 4: Prompt Integration")
    print("=" * 60)
    
    # Simulate some events first
    manager = BurstResponseManager(PersonalityMode.REGULAR)
    
    # Record some events
    for _ in range(3):
        manager.record_event(EventType.DEATH)
    manager.record_event(EventType.ACHIEVEMENT)
    
    # Get context and response
    context = manager.get_context_summary()
    burst_response = manager.get_response(EventType.DEATH)
    
    print("\nEvent Context:")
    print(format_event_context(context))
    
    print(f"\nBurst Response: {burst_response}")
    
    # Build enhanced prompt
    integrator = BurstPromptIntegrator("regular")
    
    base_prompt = """You are Celest, a gaming companion.
Be helpful and supportive to the player."""
    
    enhanced_prompt = integrator.build_prompt(
        base_prompt=base_prompt,
        event_context=context,
        burst_response=burst_response
    )
    
    print("\n\nEnhanced Prompt:")
    print("-" * 40)
    print(enhanced_prompt)


def example_5_streamtracker_integration():
    """Example 5: How to integrate with StreamTracker."""
    print("\n" + "=" * 60)
    print("Example 5: StreamTracker Integration")
    print("=" * 60)
    
    print("""
# In your StreamTracker app.py or overlay handler:

from burst_responses import get_burst_manager, EventType
from burst_prompt_integration import BurstPromptIntegrator

# Initialize burst manager (do this once at startup)
burst_manager = get_burst_manager(
    personality="regular",
    history_file="data/burst_history.json"
)

# Initialize prompt integrator
prompt_integrator = BurstPromptIntegrator("regular")

# When an achievement is unlocked:
def on_achievement_unlocked(achievement_data):
    # Get burst response
    response = burst_manager.get_burst_response("achievement", 
        achievement_name=achievement_data['name'],
        rarity_percent=achievement_data.get('rarity', 100)
    )
    
    # Get context for prompts
    context = burst_manager.get_context_summary()
    
    # Build enhanced prompt for your avatar
    enhanced_prompt = prompt_integrator.build_prompt(
        base_prompt=YOUR_AVATAR_BASE_PROMPT,
        event_context=context,
        burst_response=response['response']
    )
    
    # Send to your avatar/AI system
    avatar_response = your_ai_system.generate(enhanced_prompt)
    
    # Also broadcast to overlay/chat
    websocket_broadcast({
        "type": "burst_response",
        "event": "achievement",
        "message": response['response']
    })
""")


def example_6_api_usage():
    """Example 6: API-style usage for backend integration."""
    print("\n" + "=" * 60)
    print("Example 6: API-Style Usage")
    print("=" * 60)
    
    # Get the global manager
    manager = get_burst_manager("unhinged")
    
    # API-style response
    result = manager.get_burst_response(
        event_type="killstreak",
        streak_count=7,
        game_name="Apex Legends"
    )
    
    print("\nAPI Response:")
    print(json.dumps(result, indent=2))


def example_7_convenience_functions():
    """Example 7: Using convenience functions."""
    print("\n" + "=" * 60)
    print("Example 7: Convenience Functions")
    print("=" * 60)
    
    # Direct function calls without managing a manager instance
    print("\nAchievement (Regular):")
    print(f"  {on_achievement('regular', achievement_name='Headshot')}")
    
    print("\nDeath (Unhinged):")
    print(f"  {on_death('unhinged', cause='explosion')}")
    
    print("\nKillstreak (Regular):")
    print(f"  {on_killstreak(5, 'regular')}")
    
    print("\nExplosion (Viewer):")
    print(f"  {on_explosion('viewer', survived=True)}")


def example_8_prompt_templates():
    """Example 8: Using pre-built prompt templates."""
    print("\n" + "=" * 60)
    print("Example 8: Pre-built Prompt Templates")
    print("=" * 60)
    
    # Get a pre-built template
    template = get_prompt_template("celest_regular")
    
    if template:
        context = {
            "recent_death_count": 2,
            "recent_achievement_count": 1,
            "recent_kill_count": 4,
            "is_on_killstreak": True,
            "is_struggling": False,
            "is_tilted": False,
            "last_event_type": "killstreak"
        }
        
        event_context = format_event_context(context)
        
        rendered = template.render(
            event_context=event_context,
            burst_response="ON FIRE! 🔥"
        )
        
        print(rendered)


def demo_all():
    """Run all examples."""
    example_1_basic_usage()
    example_2_personality_modes()
    example_3_death_streak()
    example_4_prompt_integration()
    example_5_streamtracker_integration()
    example_6_api_usage()
    example_7_convenience_functions()
    example_8_prompt_templates()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    demo_all()
