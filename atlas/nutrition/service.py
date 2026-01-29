"""
ATLAS Nutrition Service

Orchestrates meal logging with automatic nutrition calculation.

Usage:
    service = NutritionService()
    record = await service.log_meal("100g chicken breast, cup of rice, broccoli")
    print(f"Logged: {record.nutrients.calories} calories")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from atlas.nutrition.food_parser import FoodItem, FoodParser
from atlas.nutrition.usda_client import USDAFoodData

logger = logging.getLogger(__name__)


@dataclass
class NutrientInfo:
    """Nutritional information for a meal or food item."""

    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0
    sugar_g: float = 0.0
    sodium_mg: float = 0.0

    def __add__(self, other: "NutrientInfo") -> "NutrientInfo":
        """Add two NutrientInfo objects together."""
        return NutrientInfo(
            calories=self.calories + other.calories,
            protein_g=self.protein_g + other.protein_g,
            carbs_g=self.carbs_g + other.carbs_g,
            fat_g=self.fat_g + other.fat_g,
            fiber_g=self.fiber_g + other.fiber_g,
            sugar_g=self.sugar_g + other.sugar_g,
            sodium_mg=self.sodium_mg + other.sodium_mg,
        )

    def to_dict(self) -> dict:
        return {
            "calories": round(self.calories, 1),
            "protein_g": round(self.protein_g, 1),
            "carbs_g": round(self.carbs_g, 1),
            "fat_g": round(self.fat_g, 1),
            "fiber_g": round(self.fiber_g, 1),
            "sugar_g": round(self.sugar_g, 1),
            "sodium_mg": round(self.sodium_mg, 1),
        }

    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"{self.calories:.0f} cal, "
            f"{self.protein_g:.0f}g protein, "
            f"{self.carbs_g:.0f}g carbs, "
            f"{self.fat_g:.0f}g fat"
        )


@dataclass
class MealRecord:
    """A logged meal with nutrition data."""

    timestamp: datetime
    items: list[FoodItem]
    nutrients: NutrientInfo
    raw_input: str
    notes: Optional[str] = None
    item_details: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "items": [item.to_dict() for item in self.items],
            "nutrients": self.nutrients.to_dict(),
            "raw_input": self.raw_input,
            "notes": self.notes,
            "item_details": self.item_details,
        }

    def summary(self) -> str:
        """Human-readable summary for voice confirmation."""
        return f"Logged meal. {self.nutrients.summary()}"


class NutritionService:
    """
    Service for logging meals with automatic nutrition calculation.

    Workflow:
    1. Parse natural language input into FoodItems
    2. Look up each food in USDA FDC database
    3. Calculate scaled nutrients based on quantities
    4. Store in semantic memory
    """

    def __init__(
        self,
        usda_client: Optional[USDAFoodData] = None,
        parser: Optional[FoodParser] = None,
    ):
        """
        Initialize nutrition service.

        Args:
            usda_client: USDA FDC API client (creates one if not provided)
            parser: Food parser (creates one if not provided)
        """
        self.usda = usda_client or USDAFoodData()
        self.parser = parser or FoodParser()

    async def parse_meal_input(self, text: str) -> list[FoodItem]:
        """
        Parse natural language meal input.

        Args:
            text: Natural language description (e.g., "100g chicken, cup of rice")

        Returns:
            List of parsed FoodItem objects
        """
        return await self.parser.parse(text)

    async def lookup_nutrition(self, item: FoodItem) -> tuple[NutrientInfo, dict]:
        """
        Look up nutrition for a single food item.

        Args:
            item: Parsed food item with name, quantity, unit

        Returns:
            Tuple of (NutrientInfo, detail_dict with fdc_id and match info)
        """
        from atlas.nutrition.usda_client import USDAAPIError, USDAAPIRateLimitError

        # Search for the food
        try:
            foods = await self.usda.search_foods(item.name, page_size=3)
        except USDAAPIRateLimitError:
            logger.warning(f"Rate limited looking up: {item.name}")
            return NutrientInfo(), {
                "food": item.name,
                "matched": False,
                "error": "API rate limited. Try again later.",
            }
        except USDAAPIError as e:
            logger.error(f"USDA API error looking up {item.name}: {e}")
            return NutrientInfo(), {
                "food": item.name,
                "matched": False,
                "error": str(e),
            }

        if not foods:
            logger.warning(f"No USDA match for: {item.name}")
            return NutrientInfo(), {"food": item.name, "matched": False}

        # Use first match (most relevant)
        best_match = foods[0]

        # Get nutrients per 100g
        try:
            nutrients_raw = await self.usda.get_nutrients(best_match.fdc_id)
        except USDAAPIError as e:
            logger.error(f"Error getting nutrients for {item.name}: {e}")
            return NutrientInfo(), {
                "food": item.name,
                "matched": True,
                "fdc_id": best_match.fdc_id,
                "description": best_match.description,
                "error": str(e),
            }

        if not nutrients_raw:
            logger.warning(f"No nutrients for fdc_id: {best_match.fdc_id}")
            return NutrientInfo(), {
                "food": item.name,
                "matched": True,
                "fdc_id": best_match.fdc_id,
                "description": best_match.description,
            }

        # Estimate grams
        quantity_g = self.parser.estimate_grams(item)

        # Scale nutrients
        scale = quantity_g / 100.0
        nutrients = NutrientInfo(
            calories=nutrients_raw.get("calories", 0) * scale,
            protein_g=nutrients_raw.get("protein", 0) * scale,
            carbs_g=nutrients_raw.get("carbs", 0) * scale,
            fat_g=nutrients_raw.get("fat", 0) * scale,
            fiber_g=nutrients_raw.get("fiber", 0) * scale,
            sugar_g=nutrients_raw.get("sugar", 0) * scale,
            sodium_mg=nutrients_raw.get("sodium", 0) * scale,
        )

        detail = {
            "food": item.name,
            "matched": True,
            "fdc_id": best_match.fdc_id,
            "description": best_match.description,
            "quantity_g": quantity_g,
            "nutrients_per_100g": nutrients_raw,
        }

        return nutrients, detail

    async def log_meal(
        self, text: str, notes: Optional[str] = None, store: bool = True
    ) -> MealRecord:
        """
        Log a meal with automatic nutrition calculation.

        Args:
            text: Natural language meal description
            notes: Optional notes to attach
            store: Whether to store in semantic memory (default True)

        Returns:
            MealRecord with parsed items and total nutrients
        """
        logger.info(f"Logging meal: {text}")

        # Parse input
        items = await self.parse_meal_input(text)
        if not items:
            logger.warning(f"Could not parse meal: {text}")
            # Return empty record
            return MealRecord(
                timestamp=datetime.now(),
                items=[],
                nutrients=NutrientInfo(),
                raw_input=text,
                notes=notes,
            )

        # Look up nutrition for each item
        total_nutrients = NutrientInfo()
        item_details = []

        for item in items:
            nutrients, detail = await self.lookup_nutrition(item)
            total_nutrients = total_nutrients + nutrients
            item_details.append(detail)
            logger.debug(f"  {item.name}: {nutrients.calories:.0f} cal")

        # Create record
        record = MealRecord(
            timestamp=datetime.now(),
            items=items,
            nutrients=total_nutrients,
            raw_input=text,
            notes=notes,
            item_details=item_details,
        )

        # Store in semantic memory
        if store:
            await self._store_meal(record)

        logger.info(f"Logged meal: {record.nutrients.summary()}")
        return record

    async def _store_meal(self, record: MealRecord) -> None:
        """Store meal record in memory store."""
        try:
            from atlas.memory.store import get_store
            import json

            store = get_store()

            # Create a descriptive text for storage
            items_text = ", ".join(item.name for item in record.items)
            # Include metadata as JSON in content for searchability
            content = json.dumps({
                "text": f"Meal logged: {items_text}. {record.nutrients.summary()}",
                "type": "meal",
                "timestamp": record.timestamp.isoformat(),
                "calories": record.nutrients.calories,
                "protein_g": record.nutrients.protein_g,
                "carbs_g": record.nutrients.carbs_g,
                "fat_g": record.nutrients.fat_g,
                "items": [item.to_dict() for item in record.items],
                "raw_input": record.raw_input,
            })

            store.add_memory(
                content=content,
                importance=0.5,
                memory_type="meal",
                source="classifier:health:meals",
            )
            logger.info("Stored meal in memory store")

            # Award XP for meal logging (non-blocking)
            self._award_meal_xp()
        except ImportError:
            logger.warning("MemoryStore not available, meal not stored")
        except Exception as e:
            logger.error(f"Failed to store meal: {e}")

    def _award_meal_xp(self) -> None:
        """Award XP for logging a meal (non-blocking)."""
        try:
            from atlas.gamification.xp_service import award_xp_safe_async, XP_TABLE
            xp = XP_TABLE.get("meal_log", 40)
            award_xp_safe_async("nutrition", xp, "meal_log")
        except Exception as e:
            # XP failure should never break meal logging
            logger.debug(f"XP award skipped: {e}")

    async def get_daily_totals(self, query_date: Optional[datetime] = None) -> NutrientInfo:
        """
        Get total nutrition for a day.

        Args:
            query_date: Date to get totals for (defaults to today)

        Returns:
            NutrientInfo with daily totals
        """
        try:
            from atlas.memory.store import get_store
            import json

            store = get_store()

            if query_date is None:
                query_date = datetime.now()

            date_str = query_date.strftime("%Y-%m-%d")

            # Search for meals on this date using full-text search
            results = store.search_fts(f"meal {date_str}", limit=50)

            total = NutrientInfo()
            for result in results:
                content = result.memory.content
                # Parse JSON content if stored as JSON
                try:
                    data = json.loads(content)
                    if data.get("type") == "meal" and date_str in data.get("timestamp", ""):
                        total.calories += data.get("calories", 0)
                        total.protein_g += data.get("protein_g", 0)
                        total.carbs_g += data.get("carbs_g", 0)
                        total.fat_g += data.get("fat_g", 0)
                except json.JSONDecodeError:
                    # Not a JSON meal record, skip
                    continue

            return total

        except ImportError:
            logger.warning("MemoryStore not available")
            return NutrientInfo()
        except Exception as e:
            logger.error(f"Failed to get daily totals: {e}")
            return NutrientInfo()
