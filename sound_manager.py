class SoundManager:
    """Manages sound playback based on achievement rarity."""

    def __init__(self, base_volume=0.5):
        """Initializes the rarity tiers and their sound configurations."""
        self.base_volume = base_volume
        self.tiers = [
            {
                "name": "legendary",
                "threshold": 1.0,
                "sound_url": "/assets/sounds/legendary.mp3",
                "volume_multiplier": 1.2,
                "color": "#FFD700"  # Gold
            },
            {
                "name": "ultra_rare",
                "threshold": 5.0,
                "sound_url": "/assets/sounds/ultra_rare.mp3",
                "volume_multiplier": 1.1,
                "color": "#FF4500"  # Orange Red
            },
            {
                "name": "rare",
                "threshold": 20.0,
                "sound_url": "/assets/sounds/rare.mp3",
                "volume_multiplier": 1.0,
                "color": "#9370DB"  # Purple
            },
            {
                "name": "uncommon",
                "threshold": 50.0,
                "sound_url": "/assets/sounds/uncommon.mp3",
                "volume_multiplier": 0.9,
                "color": "#4169E1"  # Royal Blue
            },
            {
                "name": "common",
                "threshold": 100.0,
                "sound_url": "/assets/sounds/common.mp3",
                "volume_multiplier": 0.8,
                "color": "#808080"  # Gray
            }
        ]

    def get_tier_for_rarity(self, percent):
        """Returns the tier name for a given rarity percentage."""
        if percent < 0:
            percent = 100.0
        
        for tier in self.tiers:
            if percent <= tier["threshold"]:
                return tier["name"]
        return "common"

    def get_sound_for_rarity(self, percent):
        """
        Determines the appropriate sound configuration for a given rarity percentage.
        
        Args:
            percent (float): The global unlock percentage of the achievement.

        Returns:
            dict: A dictionary containing 'url', 'volume', 'tier', and 'color'.
        """
        if percent < 0:
            percent = 100.0

        for tier in self.tiers:
            if percent <= tier["threshold"]:
                return {
                    "url": tier["sound_url"],
                    "volume": tier["volume_multiplier"] * self.base_volume,
                    "tier": tier["name"],
                    "color": tier["color"]
                }
        
        return {
            "url": self.tiers[-1]["sound_url"],
            "volume": self.tiers[-1]["volume_multiplier"] * self.base_volume,
            "tier": self.tiers[-1]["name"],
            "color": self.tiers[-1]["color"]
        }

    def play_achievement_sound(self, achievement_data):
        """
        Selects a sound based on achievement data and returns its configuration.

        Args:
            achievement_data (dict): A dictionary representing the unlocked achievement.
                                     Must contain a 'rarity' or 'global_percent' key.

        Returns:
            dict: The sound configuration (url, volume, tier, color) for the achievement's rarity.
        """
        global_percent = achievement_data.get("rarity", 
                              achievement_data.get("global_percent", 100.0))
        sound_config = self.get_sound_for_rarity(global_percent)
        
        print(f"🔊 Sound for '{achievement_data.get('name', 'Unknown')}' "
              f"({global_percent}% rarity): {sound_config['tier'].upper()}")
              
        return sound_config

    def get_all_tiers(self):
        """Returns all tier definitions for UI configuration."""
        return self.tiers
