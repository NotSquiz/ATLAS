"""
Sprite loader for OSRS-style Command Centre.

Reads sprite mappings from config/ui/sprites.json.
To customize visuals, edit the JSON file - no code changes needed.

Usage:
    from atlas.ui.sprite_loader import SpriteLoader

    loader = SpriteLoader()

    # Get a skill icon (returns CTkImage or None)
    strength_icon = loader.get_skill("strength", size=(32, 32))

    # Get an inventory item
    shark = loader.get_inventory("row3_nutrition", "healthy_meal", size=(36, 36))

    # Get an orb icon
    hp_orb = loader.get_orb("body_battery", size=(24, 24))
"""

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Check if we're in a GUI context
try:
    from PIL import Image
    import customtkinter as ctk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    logger.warning("PIL/customtkinter not available - sprite loading disabled")


class SpriteLoader:
    """Load and cache sprites based on JSON configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize sprite loader.

        Args:
            config_path: Path to sprites.json. Defaults to config/ui/sprites.json
        """
        if config_path is None:
            # Find project root (where config/ lives)
            self.project_root = Path(__file__).parent.parent.parent
            config_path = self.project_root / "config" / "ui" / "sprites.json"
        else:
            self.project_root = config_path.parent.parent.parent

        self.config_path = config_path
        self.config = self._load_config()
        self.sprite_dir = self.project_root / self.config.get("_sprite_dir", "assets/sprites/")
        self.fallback = self.config.get("_fallback", "placeholder.png")

        # Cache loaded images to avoid re-reading files
        self._cache: dict[str, "ctk.CTkImage"] = {}

        logger.info(f"SpriteLoader initialized. Sprite dir: {self.sprite_dir}")

    def _load_config(self) -> dict:
        """Load sprite configuration from JSON."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Sprite config not found: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid sprite config JSON: {e}")
            return {}

    def reload_config(self) -> None:
        """Reload configuration from disk. Call after editing sprites.json."""
        self.config = self._load_config()
        self._cache.clear()
        logger.info("Sprite config reloaded")

    def _load_image(self, filename: str, size: Tuple[int, int]) -> Optional["ctk.CTkImage"]:
        """
        Load a sprite image as CTkImage.

        Args:
            filename: Sprite filename (relative to sprite_dir)
            size: (width, height) tuple for display size

        Returns:
            CTkImage or None if loading fails
        """
        if not GUI_AVAILABLE:
            return None

        cache_key = f"{filename}_{size[0]}x{size[1]}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        sprite_path = self.sprite_dir / filename

        # Try primary path
        if not sprite_path.exists():
            # Try fallback
            fallback_path = self.sprite_dir / self.fallback
            if fallback_path.exists():
                sprite_path = fallback_path
                logger.debug(f"Using fallback for missing sprite: {filename}")
            else:
                logger.warning(f"Sprite not found (no fallback): {filename}")
                return None

        try:
            pil_image = Image.open(sprite_path)

            # Handle transparency
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')

            ctk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=size
            )

            self._cache[cache_key] = ctk_image
            return ctk_image

        except Exception as e:
            logger.error(f"Failed to load sprite {filename}: {e}")
            return None

    def get_skill(self, skill_name: str, size: Tuple[int, int] = (32, 32)) -> Optional["ctk.CTkImage"]:
        """
        Get a skill icon.

        Args:
            skill_name: One of: strength, endurance, mobility, nutrition,
                       focus, learning, reflection, creation,
                       presence, service, courage, consistency
            size: Display size (width, height)

        Returns:
            CTkImage or None
        """
        skills = self.config.get("skills", {})
        filename = skills.get(skill_name)

        if not filename:
            logger.warning(f"Unknown skill: {skill_name}")
            return None

        return self._load_image(filename, size)

    def get_orb(self, orb_name: str, size: Tuple[int, int] = (24, 24)) -> Optional["ctk.CTkImage"]:
        """
        Get an orb icon (body_battery, sleep_score, hrv_status, streak).
        """
        orbs = self.config.get("orbs", {})
        filename = orbs.get(orb_name)

        if not filename:
            logger.warning(f"Unknown orb: {orb_name}")
            return None

        return self._load_image(filename, size)

    def get_inventory(
        self,
        row: str,
        item: str,
        size: Tuple[int, int] = (36, 36)
    ) -> Optional["ctk.CTkImage"]:
        """
        Get an inventory item sprite.

        Args:
            row: Row key (row1_workouts, row2_supplements, etc.)
            item: Item key within the row
            size: Display size

        Returns:
            CTkImage or None
        """
        inventory = self.config.get("inventory", {})
        row_items = inventory.get(row, {})
        filename = row_items.get(item)

        if not filename:
            logger.warning(f"Unknown inventory item: {row}/{item}")
            return None

        return self._load_image(filename, size)

    def get_tab(self, tab_name: str, size: Tuple[int, int] = (28, 28)) -> Optional["ctk.CTkImage"]:
        """Get a tab icon (inventory, equipment, skills, quests, settings)."""
        tabs = self.config.get("tabs", {})
        filename = tabs.get(tab_name)

        if not filename:
            logger.warning(f"Unknown tab: {tab_name}")
            return None

        return self._load_image(filename, size)

    def get_nav(self, nav_name: str, size: Tuple[int, int] = (20, 20)) -> Optional["ctk.CTkImage"]:
        """Get a navigation button icon."""
        nav = self.config.get("nav_buttons", {})
        filename = nav.get(nav_name)

        if not filename:
            logger.warning(f"Unknown nav button: {nav_name}")
            return None

        return self._load_image(filename, size)

    def get_misc(self, name: str, size: Tuple[int, int] = (32, 32)) -> Optional["ctk.CTkImage"]:
        """Get a miscellaneous UI element sprite."""
        misc = self.config.get("misc", {})
        filename = misc.get(name)

        if not filename:
            logger.warning(f"Unknown misc sprite: {name}")
            return None

        return self._load_image(filename, size)

    def get_raw(self, filename: str, size: Tuple[int, int] = (32, 32)) -> Optional["ctk.CTkImage"]:
        """
        Load a sprite directly by filename (for custom/unlisted sprites).

        Args:
            filename: Sprite filename in assets/sprites/
            size: Display size
        """
        return self._load_image(filename, size)

    def list_available(self) -> dict:
        """
        List all configured sprites by category.

        Returns:
            Dict with categories and their sprite mappings
        """
        return {
            "skills": list(self.config.get("skills", {}).keys()),
            "orbs": list(self.config.get("orbs", {}).keys()),
            "inventory_rows": list(self.config.get("inventory", {}).keys()),
            "tabs": list(self.config.get("tabs", {}).keys()),
            "nav_buttons": list(self.config.get("nav_buttons", {}).keys()),
            "misc": list(self.config.get("misc", {}).keys()),
        }

    def check_missing(self) -> list[str]:
        """
        Check which configured sprites are missing from disk.

        Returns:
            List of missing sprite filenames
        """
        missing = []

        def check_dict(d: dict, prefix: str = ""):
            for key, value in d.items():
                if key.startswith("_"):
                    continue
                if isinstance(value, dict):
                    check_dict(value, f"{prefix}{key}/")
                elif isinstance(value, str) and value.endswith(".png"):
                    sprite_path = self.sprite_dir / value
                    if not sprite_path.exists():
                        missing.append(f"{prefix}{key}: {value}")

        check_dict(self.config)
        return missing


# Singleton instance for easy import
_loader: Optional[SpriteLoader] = None

def get_sprite_loader() -> SpriteLoader:
    """Get or create the global sprite loader instance."""
    global _loader
    if _loader is None:
        _loader = SpriteLoader()
    return _loader


if __name__ == "__main__":
    # Quick test / diagnostic
    import sys

    loader = SpriteLoader()

    print("=== Sprite Loader Diagnostic ===\n")
    print(f"Config path: {loader.config_path}")
    print(f"Sprite dir: {loader.sprite_dir}")
    print(f"Sprite dir exists: {loader.sprite_dir.exists()}")
    print()

    print("Available sprites:")
    for category, items in loader.list_available().items():
        # Filter out comments
        items = [i for i in items if not i.startswith("_")]
        print(f"  {category}: {len(items)} items")
    print()

    missing = loader.check_missing()
    if missing:
        print(f"Missing sprites ({len(missing)}):")
        for m in missing[:10]:  # Show first 10
            print(f"  - {m}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")
    else:
        print("All configured sprites found!")

    sys.exit(0 if not missing else 1)
