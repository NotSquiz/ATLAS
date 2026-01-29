"""
Food Parser using Local LLM (Ollama) or Claude API

Parses natural language food descriptions into structured items.
Example: "5 crackers with 100g camembert, 50g salami"
    → [FoodItem(name="crackers", quantity=5, unit="piece"), ...]

Prefers local Ollama for parsing (free, fast).
Falls back to Claude API if configured.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FoodItem:
    """A parsed food item with quantity and unit."""

    name: str
    quantity: float
    unit: str  # "g", "piece", "cup", "oz", "ml", "tbsp", "tsp"

    def to_dict(self) -> dict:
        return {"name": self.name, "quantity": self.quantity, "unit": self.unit}

    @classmethod
    def from_dict(cls, data: dict) -> "FoodItem":
        return cls(
            name=data.get("name", data.get("food", "")),
            quantity=float(data.get("quantity", 1)),
            unit=data.get("unit", "piece"),
        )


# Common unit conversions to grams (approximate)
UNIT_TO_GRAMS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "oz": 28.35,
    "ounce": 28.35,
    "ounces": 28.35,
    "lb": 453.6,
    "pound": 453.6,
    "pounds": 453.6,
    "cup": 240.0,  # Approximate for most foods
    "cups": 240.0,
    "tbsp": 15.0,
    "tablespoon": 15.0,
    "tablespoons": 15.0,
    "tsp": 5.0,
    "teaspoon": 5.0,
    "teaspoons": 5.0,
    "ml": 1.0,  # Approximate (depends on density)
    "piece": None,  # Needs food-specific lookup
    "pieces": None,
    "slice": None,
    "slices": None,
    "serving": None,
}

# Average weights for common "piece" items
PIECE_WEIGHTS = {
    "egg": 50,
    "eggs": 50,
    "banana": 120,
    "bananas": 120,
    "apple": 180,
    "apples": 180,
    "orange": 130,
    "oranges": 130,
    "cracker": 10,
    "crackers": 10,
    "cookie": 30,
    "cookies": 30,
    "slice of bread": 30,
    "bread slice": 30,
    "tomato": 150,
    "tomatoes": 150,
    "olive": 4,
    "olives": 4,
}


class FoodParser:
    """
    Parses natural language food input into structured FoodItem objects.

    Uses regex patterns for simple cases, falls back to Claude for complex input.
    """

    # Pattern: "100g chicken" or "100 g chicken"
    QUANTITY_UNIT_PATTERN = re.compile(
        r"(\d+(?:\.\d+)?)\s*(g|gram|grams|kg|oz|ounce|ounces|lb|pound|pounds|cup|cups|tbsp|tablespoon|tablespoons|tsp|teaspoon|teaspoons|ml)\s+(.+)",
        re.IGNORECASE,
    )

    # Pattern: "5 crackers" or "2 eggs"
    COUNT_PATTERN = re.compile(
        r"(\d+(?:\.\d+)?)\s+(.+)",
        re.IGNORECASE,
    )

    # Pattern: "a banana" or "an apple"
    ARTICLE_PATTERN = re.compile(
        r"^(?:a|an)\s+(.+)",
        re.IGNORECASE,
    )

    def __init__(self, use_llm: bool = True, prefer_local: bool = True):
        """
        Initialize parser.

        Args:
            use_llm: Whether to use LLM for complex parsing. If False, uses regex only.
            prefer_local: If True, prefer local Ollama over Claude API (default True).
        """
        self.prefer_local = prefer_local
        self.use_api = os.environ.get("ANTHROPIC_API_KEY")
        self.use_llm = use_llm and (prefer_local or self.use_api)
        self._ollama_client = None

    def _parse_single_regex(self, text: str) -> Optional[FoodItem]:
        """Try to parse a single food item using regex patterns."""
        text = text.strip()

        # Try "100g chicken" pattern
        match = self.QUANTITY_UNIT_PATTERN.match(text)
        if match:
            quantity = float(match.group(1))
            unit = match.group(2).lower()
            name = match.group(3).strip()
            return FoodItem(name=name, quantity=quantity, unit=unit)

        # Try "5 crackers" pattern
        match = self.COUNT_PATTERN.match(text)
        if match:
            quantity = float(match.group(1))
            name = match.group(2).strip()
            return FoodItem(name=name, quantity=quantity, unit="piece")

        # Try "a banana" pattern
        match = self.ARTICLE_PATTERN.match(text)
        if match:
            name = match.group(1).strip()
            return FoodItem(name=name, quantity=1, unit="piece")

        # Just a food name
        if text:
            return FoodItem(name=text, quantity=1, unit="piece")

        return None

    def _split_foods(self, text: str) -> list[str]:
        """Split input into individual food items."""
        # Split on common separators
        separators = [",", " and ", " with ", " plus ", ";"]
        items = [text]

        for sep in separators:
            new_items = []
            for item in items:
                new_items.extend(item.split(sep))
            items = new_items

        return [item.strip() for item in items if item.strip()]

    def parse_regex(self, text: str) -> list[FoodItem]:
        """
        Parse food input using regex patterns only.

        Args:
            text: Natural language food description

        Returns:
            List of parsed FoodItem objects
        """
        # Remove common prefixes
        text = re.sub(r"^(log meal:?|had|ate|eating)\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^(for breakfast|for lunch|for dinner):?\s*", "", text, flags=re.IGNORECASE)

        items = self._split_foods(text)
        results = []

        for item_text in items:
            parsed = self._parse_single_regex(item_text)
            if parsed:
                results.append(parsed)

        return results

    async def parse_llm(self, text: str) -> list[FoodItem]:
        """
        Parse food input using Claude LLM.

        Args:
            text: Natural language food description

        Returns:
            List of parsed FoodItem objects
        """
        try:
            import anthropic
        except ImportError:
            logger.warning("anthropic package not installed, falling back to regex")
            return self.parse_regex(text)

        client = anthropic.Anthropic()

        prompt = f"""Parse this food log into structured items. Extract each food with its quantity and unit.

Input: "{text}"

Rules:
- Use "g" for grams, "piece" for countable items
- If no quantity given, assume 1
- Common foods: "crackers" = piece, "cheese" = g, "bread" = slice
- Return valid JSON array only, no explanation

Example output:
[{{"name": "crackers", "quantity": 5, "unit": "piece"}}, {{"name": "camembert cheese", "quantity": 100, "unit": "g"}}]

Output:"""

        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract JSON from response
            content = response.content[0].text.strip()

            # Find JSON array in response
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                items_data = json.loads(match.group())
                return [FoodItem.from_dict(item) for item in items_data]

        except Exception as e:
            logger.error(f"LLM parsing failed: {e}, falling back to regex")

        return self.parse_regex(text)

    async def parse_local(self, text: str) -> list[FoodItem]:
        """
        Parse food input using local Ollama LLM.

        Args:
            text: Natural language food description

        Returns:
            List of parsed FoodItem objects
        """
        from atlas.llm.local import get_client

        if self._ollama_client is None:
            self._ollama_client = get_client()

        # Check if Ollama is available
        if not self._ollama_client.is_available():
            logger.warning("Ollama not available, falling back to regex")
            return self.parse_regex(text)

        prompt = f"""Parse this food log into structured items. Extract each food with quantity and unit.

Input: "{text}"

Rules:
- Use "g" for grams, "piece" for countable items, "cup" for cups
- If no quantity given, assume 1
- Return ONLY a JSON array, no explanation
- Example: [{{"name": "banana pancakes", "quantity": 3, "unit": "piece"}}, {{"name": "coffee", "quantity": 1, "unit": "cup"}}]

Output:"""

        try:
            response = await self._ollama_client.agenerate(
                prompt=prompt,
                temperature=0.3,  # Lower temp for more consistent JSON
                max_tokens=300,
            )

            content = response.content.strip()
            logger.debug(f"Ollama response: {content}")

            # Find JSON array in response
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                items_data = json.loads(match.group())
                return [FoodItem.from_dict(item) for item in items_data]

        except Exception as e:
            logger.error(f"Local LLM parsing failed: {e}, falling back to regex")

        return self.parse_regex(text)

    async def parse(self, text: str) -> list[FoodItem]:
        """
        Parse food input into structured items.

        Priority: Local Ollama → Claude API → Regex

        Args:
            text: Natural language food description

        Returns:
            List of parsed FoodItem objects
        """
        # Try regex first for simple cases
        regex_result = self.parse_regex(text)

        # If regex found clear results, use them
        if regex_result and all(
            item.quantity > 0 and item.name for item in regex_result
        ):
            return regex_result

        # For complex cases, try LLM
        if self.use_llm:
            # Prefer local Ollama (free, fast)
            if self.prefer_local:
                return await self.parse_local(text)
            # Fall back to Claude API if configured
            if self.use_api:
                return await self.parse_llm(text)

        return regex_result

    def estimate_grams(self, item: FoodItem) -> float:
        """
        Estimate weight in grams for a food item.

        Args:
            item: Parsed food item

        Returns:
            Estimated weight in grams
        """
        unit = item.unit.lower()

        # Direct conversion
        if unit in UNIT_TO_GRAMS and UNIT_TO_GRAMS[unit] is not None:
            return item.quantity * UNIT_TO_GRAMS[unit]

        # Look up piece weight
        name_lower = item.name.lower()
        for food_name, weight in PIECE_WEIGHTS.items():
            if food_name in name_lower:
                return item.quantity * weight

        # Default estimate for unknown pieces
        logger.warning(f"Unknown piece weight for: {item.name}, estimating 50g")
        return item.quantity * 50.0
