# Nutrition API Integration Design

## Status: DESIGN COMPLETE

## User Request
> "when I say: log 'meal' and it's classified and stored, can we also have an API attached where it links to an appropriate API... I want it so I could say for example: '5 brand name crackers with 100g Camembert, 50g salami, 50g green olives, 1 tomato' and it will route the info and do the calcs and save that"

---

## Architecture Decision

### Option A: USDA FDC + Claude NLP (Recommended)
- **Cost**: Free
- **How it works**:
  1. Claude parses natural language into structured food items
  2. USDA FDC API looks up nutrition for each item
  3. Calculate totals and store

### Option B: Edamam Nutrition API
- **Cost**: $49-799/month
- **How it works**: Single API call parses and returns nutrition
- **Verdict**: Over-budget, save for later

### Recommendation: Option A
Use Claude's NLP (already in voice pipeline) to parse food strings, then USDA FDC (free) for lookups.

---

## Data Flow

```
Voice Input: "Log meal: 5 crackers, 100g camembert, 50g salami"
                    ↓
         Voice Pipeline detects "log meal" trigger
                    ↓
         NutritionService.parse_meal_input(text)
                    ↓
         Claude NLP → structured items:
         [
           {"food": "crackers", "quantity": 5, "unit": "piece"},
           {"food": "camembert", "quantity": 100, "unit": "g"},
           {"food": "salami", "quantity": 50, "unit": "g"}
         ]
                    ↓
         For each item → USDA FDC search → get FDC ID → get nutrients
                    ↓
         Calculate totals: calories, protein, carbs, fat
                    ↓
         Store MealRecord in semantic_memory
                    ↓
         Voice confirmation: "Logged 650 calories, 35g protein"
```

---

## Components to Build

### 1. NutritionService (`atlas/nutrition/service.py`)
```python
@dataclass
class FoodItem:
    name: str
    quantity: float
    unit: str  # "g", "piece", "cup", "oz", etc.
    fdc_id: Optional[int] = None

@dataclass
class NutrientInfo:
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None

@dataclass
class MealRecord:
    timestamp: datetime
    items: List[FoodItem]
    nutrients: NutrientInfo
    raw_input: str
    notes: Optional[str] = None

class NutritionService:
    async def parse_meal_input(self, text: str) -> List[FoodItem]
    async def lookup_nutrition(self, item: FoodItem) -> NutrientInfo
    async def log_meal(self, text: str) -> MealRecord
```

### 2. USDA FDC Client (`atlas/nutrition/usda_client.py`)
From R26 templates:
```python
class USDAFoodData:
    async def search_foods(self, query: str) -> List[Dict]
    async def get_food(self, fdc_id: int) -> Dict
    async def get_nutrients(self, fdc_id: int) -> Dict[str, float]
```

### 3. Claude Food Parser (`atlas/nutrition/food_parser.py`)
```python
class FoodParser:
    async def parse(self, text: str) -> List[FoodItem]:
        """Use Claude to parse natural language food input."""
        prompt = """Parse this food log into structured items.
        Input: "5 crackers with 100g camembert, 50g salami"

        Return JSON array:
        [{"food": "crackers", "quantity": 5, "unit": "piece"},
         {"food": "camembert cheese", "quantity": 100, "unit": "g"},
         {"food": "salami", "quantity": 50, "unit": "g"}]
        """
```

### 4. Voice Pipeline Integration
Add to CAPTURE_TRIGGERS:
```python
MEAL_TRIGGERS = [
    "log meal",
    "had for breakfast",
    "had for lunch",
    "had for dinner",
    "ate",
    "eating",
]
```

Update `_handle_capture()` to detect meal logging and route to NutritionService.

### 5. MCP Tool (`atlas/mcp/server.py`)
```python
@server.tool()
async def log_meal(meal_description: str) -> str:
    """Log a meal with automatic nutrition calculation."""
    service = NutritionService()
    record = await service.log_meal(meal_description)
    return f"Logged: {record.nutrients.calories:.0f} cal, {record.nutrients.protein_g:.0f}g protein"
```

---

## USDA FDC API Details

**Endpoint**: `https://api.nal.usda.gov/fdc/v1`
**API Key**: Free at https://fdc.nal.usda.gov/api-key-signup.html

**Search Example**:
```json
POST /foods/search
{
    "query": "camembert cheese",
    "pageSize": 5,
    "dataType": ["Foundation", "SR Legacy", "Branded"]
}
```

**Key Nutrients (nutrient IDs)**:
| Nutrient | ID |
|----------|-----|
| Calories | 1008 |
| Protein | 1003 |
| Carbohydrates | 1005 |
| Fat | 1004 |
| Fiber | 1079 |
| Sugar | 2000 |
| Sodium | 1093 |

**Unit Conversion**:
USDA returns nutrients per 100g. Need to scale by quantity.

---

## Storage Strategy

Store as MealRecord in semantic_memory with source: `classifier:health:meals`

```python
await self.memory.add(
    text=record.raw_input,
    metadata={
        "type": "meal",
        "timestamp": record.timestamp.isoformat(),
        "calories": record.nutrients.calories,
        "protein_g": record.nutrients.protein_g,
        "carbs_g": record.nutrients.carbs_g,
        "fat_g": record.nutrients.fat_g,
        "items": [item.to_dict() for item in record.items],
    },
    source="classifier:health:meals"
)
```

---

## Caching Strategy

From R26: 14-30 day TTL for USDA data (updated quarterly).

```python
# Cache key: usda:{search_query_hash}
# TTL: 14 days
```

Use local SQLite for offline fallback of common foods.

---

## Voice Confirmation

```
User: "Log meal: 5 crackers, 100g camembert, 50g salami"
ATLAS: "Logged meal. 650 calories, 35g protein, 45g fat, 12g carbs."
```

---

## Implementation Steps

1. **Create `atlas/nutrition/` module**
   - `__init__.py`
   - `usda_client.py` (USDA FDC API client)
   - `food_parser.py` (Claude NLP for parsing)
   - `service.py` (main NutritionService)

2. **Get USDA API key**
   - Sign up at https://fdc.nal.usda.gov/api-key-signup.html
   - Add to `.env` as `USDA_API_KEY`

3. **Implement USDA client** (from R26 templates)

4. **Implement food parser** (Claude NLP)

5. **Implement NutritionService** (orchestrates parsing + lookup)

6. **Update voice pipeline**
   - Add meal triggers
   - Route meal logs to NutritionService

7. **Add MCP tool** (log_meal)

8. **Test with examples**:
   - "5 crackers with 100g camembert"
   - "had oatmeal with banana for breakfast"
   - "100g chicken breast, cup of rice, broccoli"

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `atlas/nutrition/__init__.py` | Create |
| `atlas/nutrition/usda_client.py` | Create |
| `atlas/nutrition/food_parser.py` | Create |
| `atlas/nutrition/service.py` | Create |
| `atlas/voice/pipeline.py` | Modify - add meal triggers |
| `atlas/mcp/server.py` | Modify - add log_meal tool |
| `.env.example` | Add USDA_API_KEY |

---

*Design complete - ready for implementation*
