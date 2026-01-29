"""
USDA FoodData Central API Client

Provides nutrition lookup for foods using the free USDA FDC database.
300,000+ foods with research-grade nutritional data.

API Key: Free at https://fdc.nal.usda.gov/api-key-signup.html
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class USDAAPIError(Exception):
    """Raised when USDA API fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class USDAAPIRateLimitError(USDAAPIError):
    """Raised when USDA API rate limit is hit."""

    pass


# Nutrient IDs in USDA FDC
NUTRIENT_IDS = {
    "calories": 1008,
    "protein": 1003,
    "carbs": 1005,
    "fat": 1004,
    "fiber": 1079,
    "sugar": 2000,
    "sodium": 1093,
}


@dataclass
class USDAFood:
    """A food item from USDA FDC."""

    fdc_id: int
    description: str
    brand_owner: Optional[str] = None
    serving_size: Optional[float] = None
    serving_unit: Optional[str] = None


class USDAFoodData:
    """
    Client for USDA FoodData Central API.

    Usage:
        client = USDAFoodData()
        foods = await client.search_foods("chicken breast")
        nutrients = await client.get_nutrients(foods[0].fdc_id)
    """

    BASE_URL = "https://api.nal.usda.gov/fdc/v1"

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        """
        Initialize USDA client.

        Args:
            api_key: USDA FDC API key. Falls back to USDA_API_KEY env var.
            cache_dir: Directory for caching responses. Defaults to ~/.cache/atlas/usda
        """
        self.api_key = api_key or os.environ.get("USDA_API_KEY", "")
        if not self.api_key:
            logger.warning("No USDA_API_KEY set. Rate limits will apply (1000 req/hour).")

        self.cache_dir = cache_dir or Path.home() / ".cache" / "atlas" / "usda"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(days=14)  # USDA data updated quarterly

    def _cache_key(self, query: str) -> Path:
        """Generate cache file path for a query."""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
        return self.cache_dir / f"{query_hash}.json"

    def _get_cached(self, query: str) -> Optional[dict]:
        """Get cached response if valid."""
        cache_file = self._cache_key(query)
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                cached_at = datetime.fromisoformat(data.get("_cached_at", "1970-01-01"))
                if datetime.now() - cached_at < self.cache_ttl:
                    logger.debug(f"Cache hit for: {query}")
                    return data.get("response")
            except (json.JSONDecodeError, ValueError):
                cache_file.unlink(missing_ok=True)
        return None

    def _set_cached(self, query: str, response: dict) -> None:
        """Cache a response."""
        cache_file = self._cache_key(query)
        cache_file.write_text(
            json.dumps({"_cached_at": datetime.now().isoformat(), "response": response})
        )

    async def search_foods(
        self, query: str, page_size: int = 5, data_types: Optional[list[str]] = None
    ) -> list[USDAFood]:
        """
        Search foods by keyword.

        Args:
            query: Search term (e.g., "chicken breast", "camembert cheese")
            page_size: Number of results (default 5)
            data_types: Filter by data type. Options:
                - "Foundation" (research-grade, most accurate)
                - "SR Legacy" (legacy USDA data)
                - "Branded" (commercial products with barcodes)

        Returns:
            List of USDAFood objects
        """
        cache_key = f"search:{query}:{page_size}"
        cached = self._get_cached(cache_key)
        if cached:
            return [USDAFood(**f) for f in cached]

        if data_types is None:
            data_types = ["Foundation", "SR Legacy", "Branded"]

        # Validate input
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(
                    f"{self.BASE_URL}/foods/search",
                    params={"api_key": self.api_key} if self.api_key else {},
                    json={
                        "query": query,
                        "pageSize": page_size,
                        "dataType": data_types,
                    },
                )

                # Check for rate limiting
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After", "60")
                    logger.warning(f"USDA API rate limited. Retry after {retry_after}s")
                    raise USDAAPIRateLimitError(
                        f"Rate limited. Retry after {retry_after} seconds.",
                        status_code=429,
                    )

                resp.raise_for_status()
                data = resp.json()

            except httpx.TimeoutException:
                logger.error(f"USDA API timeout for query: {query}")
                raise USDAAPIError("USDA API request timed out. Try again later.")
            except httpx.HTTPStatusError as e:
                logger.error(f"USDA API HTTP error: {e.response.status_code}")
                raise USDAAPIError(
                    f"USDA API error: {e.response.status_code}",
                    status_code=e.response.status_code,
                )
            except httpx.RequestError as e:
                logger.error(f"USDA API request error: {e}")
                raise USDAAPIError(f"Network error: {e}")

        foods = []
        for item in data.get("foods", []):
            foods.append(
                USDAFood(
                    fdc_id=item.get("fdcId"),
                    description=item.get("description", ""),
                    brand_owner=item.get("brandOwner"),
                    serving_size=item.get("servingSize"),
                    serving_unit=item.get("servingSizeUnit"),
                )
            )

        # Cache the results
        self._set_cached(cache_key, [f.__dict__ for f in foods])
        return foods

    async def get_food(self, fdc_id: int) -> Optional[dict]:
        """
        Get detailed food data by FDC ID.

        Args:
            fdc_id: USDA FoodData Central ID

        Returns:
            Full food data including all nutrients
        """
        cache_key = f"food:{fdc_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Validate input
        if fdc_id <= 0:
            logger.warning(f"Invalid fdc_id: {fdc_id}")
            return None

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    f"{self.BASE_URL}/food/{fdc_id}",
                    params={"api_key": self.api_key} if self.api_key else {},
                )

                if resp.status_code == 429:
                    logger.warning("USDA API rate limited")
                    raise USDAAPIRateLimitError("Rate limited", status_code=429)

                resp.raise_for_status()
                data = resp.json()

            except httpx.TimeoutException:
                logger.error(f"USDA API timeout for fdc_id {fdc_id}")
                raise USDAAPIError("USDA API request timed out")
            except httpx.HTTPStatusError as e:
                logger.error(f"USDA API HTTP error for fdc_id {fdc_id}: {e.response.status_code}")
                raise USDAAPIError(f"USDA API error: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"USDA API request error for fdc_id {fdc_id}: {e}")
                raise USDAAPIError(f"Network error: {e}")

        self._set_cached(cache_key, data)
        return data

    async def get_nutrients(self, fdc_id: int) -> dict[str, float]:
        """
        Get key nutrients for a food (per 100g).

        Args:
            fdc_id: USDA FoodData Central ID

        Returns:
            Dict with keys: calories, protein, carbs, fat, fiber, sugar, sodium
            All values are per 100g of food.
        """
        food = await self.get_food(fdc_id)
        if not food:
            return {}

        nutrients = {}
        for n in food.get("foodNutrients", []):
            nutrient_id = n.get("nutrient", {}).get("id")
            amount = n.get("amount", 0)

            for name, nid in NUTRIENT_IDS.items():
                if nutrient_id == nid:
                    nutrients[name] = amount
                    break

        return nutrients

    async def get_nutrients_scaled(
        self, fdc_id: int, quantity_g: float
    ) -> dict[str, float]:
        """
        Get nutrients scaled to a specific quantity.

        Args:
            fdc_id: USDA FoodData Central ID
            quantity_g: Amount in grams

        Returns:
            Nutrients scaled to the specified quantity
        """
        nutrients_per_100g = await self.get_nutrients(fdc_id)
        scale = quantity_g / 100.0

        return {name: value * scale for name, value in nutrients_per_100g.items()}
