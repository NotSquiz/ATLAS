"""
ATLAS Nutrition Module

Provides meal logging with automatic nutrition calculation via USDA FoodData Central.

Usage:
    from atlas.nutrition import NutritionService

    service = NutritionService()
    record = await service.log_meal("100g chicken breast, cup of rice")
    print(f"Logged: {record.nutrients.calories} calories")
"""

from atlas.nutrition.service import NutritionService, MealRecord, NutrientInfo, FoodItem
from atlas.nutrition.usda_client import USDAFoodData, USDAAPIError, USDAAPIRateLimitError
from atlas.nutrition.food_parser import FoodParser

__all__ = [
    "NutritionService",
    "MealRecord",
    "NutrientInfo",
    "FoodItem",
    "USDAFoodData",
    "USDAAPIError",
    "USDAAPIRateLimitError",
    "FoodParser",
]
