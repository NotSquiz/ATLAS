"""
ATLAS Number Parser - Voice Input to Float Conversion

Handles spoken numbers with hedging, units, and various formats.
Designed for voice-first assessment protocol.
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Word-to-number mappings
ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
}

TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

MAGNITUDE = {
    "hundred": 100,
    "thousand": 1000,
}

# Hedging words to strip
HEDGING_WORDS = [
    "about", "around", "approximately", "roughly", "maybe",
    "like", "almost", "nearly", "just under", "just over",
    "i think", "probably", "say", "let's say",
]

# Unit words to strip (and their patterns) - use word boundaries to avoid matching inside words
UNIT_PATTERNS = [
    r"\b(kg|kilos?|kilograms?)\b",
    r"\b(lbs?|pounds?)\b",
    r"\b(cm|centimeters?|centimetres?)\b",
    r"\b(mm|millimeters?|millimetres?)\b",
    r"\b(meters?|metres?)\b",  # Note: removed single 'm' to avoid false matches
    r"\b(inches?)\b",  # Note: removed 'in' to avoid matching in "ninety"
    r"\b(ft|feet|foot)\b",
    r"\b(secs?|seconds?)\b",  # Note: removed 'sec' alone
    r"\b(mins?|minutes?)\b",  # Note: removed 'min' alone
    r"\b(hrs?|hours?)\b",
    r"\b(bpm|beats per minute)\b",
    r"\b(reps?|repetitions?)\b",
    r"\b(percent|percentage)\b",  # Note: % handled separately
    r"\b(degrees?|deg)\b",
    r"\b(score|points?)\b",
]


def strip_hedging(text: str) -> str:
    """Remove hedging words from text."""
    text_lower = text.lower()
    for hedge in HEDGING_WORDS:
        text_lower = text_lower.replace(hedge, " ")
    return text_lower.strip()


def strip_units(text: str) -> str:
    """Remove unit words from text."""
    # Handle % symbol first (not a word boundary issue)
    text = text.replace("%", " ")

    for pattern in UNIT_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # Clean up multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def words_to_number(text: str) -> Optional[float]:
    """
    Convert spoken number words to float.

    Examples:
        "eighty two point five" -> 82.5
        "twenty one" -> 21.0
        "one hundred twenty three" -> 123.0
        "minus two" -> -2.0
    """
    text = text.lower().strip()

    # Handle negative numbers
    is_negative = False
    if text.startswith(("minus", "negative")):
        is_negative = True
        text = re.sub(r"^(minus|negative)\s*", "", text)

    # Handle decimals with "point"
    if " point " in text:
        parts = text.split(" point ", 1)
        whole_part = words_to_number(parts[0])
        if whole_part is None:
            return None

        # Handle decimal part (e.g., "five" -> 0.5, "five two" -> 0.52)
        decimal_text = parts[1].strip()
        decimal_value = 0.0
        decimal_place = 0.1

        for word in decimal_text.split():
            word = word.strip()
            if word in ONES:
                decimal_value += ONES[word] * decimal_place
                decimal_place *= 0.1
            elif word.isdigit():
                decimal_value += int(word) * decimal_place
                decimal_place *= 0.1
            else:
                break

        result = whole_part + decimal_value
        return -result if is_negative else result

    # Parse the whole number
    words = text.split()
    if not words:
        return None

    total = 0
    current = 0

    for word in words:
        word = word.strip().rstrip(",")

        if word in ONES:
            current += ONES[word]
        elif word in TENS:
            current += TENS[word]
        elif word == "hundred":
            current *= 100
        elif word == "thousand":
            current *= 1000
            total += current
            current = 0
        elif word == "and":
            continue
        else:
            # Skip unknown words
            continue

    total += current

    if total == 0 and "zero" not in text:
        return None

    return -float(total) if is_negative else float(total)


def parse_duration(text: str) -> Optional[float]:
    """
    Parse duration format to seconds.

    Examples:
        "5:30" -> 330.0
        "2 minutes 30 seconds" -> 150.0
        "1:23:45" -> 5025.0 (1hr 23min 45sec)
    """
    text = text.strip()

    # Try mm:ss or hh:mm:ss format
    if ":" in text:
        parts = text.split(":")
        try:
            if len(parts) == 2:
                minutes, seconds = int(parts[0]), int(parts[1])
                return float(minutes * 60 + seconds)
            elif len(parts) == 3:
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                return float(hours * 3600 + minutes * 60 + seconds)
        except ValueError:
            return None

    # Try "X minutes Y seconds" format
    minutes = 0
    seconds = 0

    min_match = re.search(r"(\d+)\s*(?:min|minutes?)", text)
    sec_match = re.search(r"(\d+)\s*(?:sec|seconds?)", text)

    if min_match:
        minutes = int(min_match.group(1))
    if sec_match:
        seconds = int(sec_match.group(1))

    if minutes > 0 or seconds > 0:
        return float(minutes * 60 + seconds)

    return None


def parse_spoken_number(text: str, allow_duration: bool = False) -> Optional[float]:
    """
    Parse spoken or typed numbers to float.

    Handles:
    - Direct float input: "82.5" -> 82.5
    - Spelled numbers: "eighty two point five" -> 82.5
    - Hedging words: "about 82.5 kilos" -> 82.5
    - Unit stripping: "twenty one percent" -> 21.0
    - Negatives: "minus two" -> -2.0
    - Duration (optional): "5:30" -> 330.0

    Args:
        text: The spoken or typed input
        allow_duration: If True, also parse mm:ss duration formats

    Returns:
        Float value or None if parsing fails
    """
    if not text or not text.strip():
        return None

    original = text
    text = text.strip()

    # 1. Try duration format first if allowed
    if allow_duration and ":" in text:
        result = parse_duration(text)
        if result is not None:
            logger.debug(f"Parsed duration '{original}' -> {result}")
            return result

    # 2. Strip hedging words
    text = strip_hedging(text)

    # 3. Strip units
    text = strip_units(text)

    # 4. Try direct float parse
    try:
        # Handle comma as decimal separator (European style)
        text_normalized = text.replace(",", ".")
        value = float(text_normalized)
        logger.debug(f"Parsed direct number '{original}' -> {value}")
        return value
    except ValueError:
        pass

    # 5. Handle "X point Y" format (e.g., "82 point 5")
    point_match = re.match(r"(\d+)\s*point\s*(\d+)", text, re.IGNORECASE)
    if point_match:
        whole = int(point_match.group(1))
        decimal_str = point_match.group(2)
        decimal = int(decimal_str) / (10 ** len(decimal_str))
        value = whole + decimal
        logger.debug(f"Parsed 'X point Y' '{original}' -> {value}")
        return value

    # 6. Try word-to-number conversion
    value = words_to_number(text)
    if value is not None:
        logger.debug(f"Parsed word number '{original}' -> {value}")
        return value

    # 7. Extract any number from the text as last resort
    num_match = re.search(r"-?\d+\.?\d*", text)
    if num_match:
        try:
            value = float(num_match.group())
            logger.debug(f"Extracted number from '{original}' -> {value}")
            return value
        except ValueError:
            pass

    logger.debug(f"Failed to parse '{original}'")
    return None


def parse_boolean(text: str) -> Optional[bool]:
    """
    Parse boolean responses.

    Examples:
        "yes" -> True
        "no" -> False
        "yeah" -> True
        "nope" -> False
        "pain-free" -> True (for the common "was it pain-free?" question)
    """
    text = text.lower().strip()

    yes_words = ["yes", "yeah", "yep", "yup", "correct", "affirmative", "true", "pain-free", "pain free"]
    no_words = ["no", "nope", "nah", "negative", "false", "not", "had pain", "painful"]

    for word in yes_words:
        if word in text:
            return True

    for word in no_words:
        if word in text:
            return False

    return None


def parse_categorical(text: str, options: list[str]) -> Optional[str]:
    """
    Parse categorical responses.

    Args:
        text: The spoken input
        options: List of valid options

    Returns:
        Matching option or None
    """
    text = text.lower().strip()

    # Direct match
    for option in options:
        if option.lower() == text:
            return option

    # Partial match
    for option in options:
        if option.lower() in text or text in option.lower():
            return option

    return None


def parse_fms_score(text: str) -> Optional[int]:
    """
    Parse FMS score (0-3).

    Examples:
        "three" -> 3
        "2" -> 2
        "pain" -> 0
        "compensation" -> 2
    """
    text = text.lower().strip()

    # Direct number
    if text.isdigit():
        score = int(text)
        if 0 <= score <= 3:
            return score

    # Word numbers
    word_map = {"zero": 0, "one": 1, "two": 2, "three": 3}
    for word, score in word_map.items():
        if word in text:
            return score

    # Keywords
    if "pain" in text:
        return 0
    if "cannot" in text or "couldn't" in text or "can't" in text:
        return 1
    if "compensation" in text or "compensat" in text:
        return 2
    if "perfect" in text or "good form" in text:
        return 3

    return None


def format_echo(value: float, unit: str = "") -> str:
    """
    Format a value for echo confirmation.

    Examples:
        format_echo(82.5, "kg") -> "82.5 kilos"
        format_echo(45, "seconds") -> "45 seconds"
    """
    # Format number nicely
    if value == int(value):
        num_str = str(int(value))
    else:
        num_str = f"{value:.1f}"

    # Friendly unit names
    unit_friendly = {
        "kg": "kilos",
        "cm": "centimeters",
        "bpm": "BPM",
        "seconds": "seconds",
        "reps": "reps",
        "%": "percent",
        "score": "",
        "degrees": "degrees",
        "ms": "milliseconds",
    }

    friendly = unit_friendly.get(unit, unit)
    if friendly:
        return f"{num_str} {friendly}"
    return num_str


def _parse_bp_number(text: str) -> Optional[int]:
    """
    Parse a blood pressure number, handling "one twenty" = 120 pattern.

    In BP context, "one twenty" means 120, not 1+20=21.
    """
    text = text.lower().strip()

    # Handle "one X" patterns for BP (one twenty = 120, one thirty = 130, etc.)
    # Sorted by length (longest first) to prefer "one forty five" over "one forty"
    bp_hundreds = [
        ("one twenty nine", 129), ("one twenty eight", 128), ("one twenty seven", 127),
        ("one twenty six", 126), ("one twenty five", 125), ("one twenty four", 124),
        ("one twenty three", 123), ("one twenty two", 122), ("one twenty one", 121),
        ("one thirty nine", 139), ("one thirty eight", 138), ("one thirty seven", 137),
        ("one thirty six", 136), ("one thirty five", 135), ("one thirty four", 134),
        ("one thirty three", 133), ("one thirty two", 132), ("one thirty one", 131),
        ("one forty five", 145), ("one forty", 140),
        ("one nineteen", 119), ("one eighteen", 118), ("one seventeen", 117),
        ("one sixteen", 116), ("one fifteen", 115), ("one fourteen", 114),
        ("one thirteen", 113), ("one twelve", 112), ("one eleven", 111),
        ("one seventy", 170), ("one eighty", 180), ("one sixty", 160),
        ("one fifty", 150), ("one thirty", 130), ("one twenty", 120),
        ("one ten", 110),
    ]

    for pattern, value in bp_hundreds:
        if text == pattern or text.startswith(pattern):
            return value

    # Fall back to standard parsing
    value = parse_spoken_number(text)
    return int(value) if value is not None else None


def parse_blood_pressure(text: str) -> tuple[Optional[int], Optional[int]]:
    """
    Parse blood pressure from natural speech.

    Examples:
        "120 over 80" -> (120, 80)
        "one twenty over eighty" -> (120, 80)
        "120/80" -> (120, 80)
        "120" -> (120, None)  # Only systolic given

    Returns:
        (systolic, diastolic) or (None, None) if parsing fails
    """
    text = text.lower().strip()

    # Try slash format: "120/80"
    if "/" in text:
        parts = text.split("/")
        if len(parts) == 2:
            try:
                systolic = int(parts[0].strip())
                diastolic = int(parts[1].strip())
                return (systolic, diastolic)
            except ValueError:
                pass

    # Try "over" format: "120 over 80"
    if " over " in text:
        parts = text.split(" over ")
        if len(parts) == 2:
            systolic = _parse_bp_number(parts[0])
            diastolic = _parse_bp_number(parts[1])
            if systolic is not None and diastolic is not None:
                return (systolic, diastolic)

    # Try "on" format: "120 on 80" (less common)
    if " on " in text:
        parts = text.split(" on ")
        if len(parts) == 2:
            systolic = _parse_bp_number(parts[0])
            diastolic = _parse_bp_number(parts[1])
            if systolic is not None and diastolic is not None:
                return (systolic, diastolic)

    # Single number - just systolic
    value = _parse_bp_number(text)
    if value is not None:
        return (value, None)

    return (None, None)


def parse_weight_reps(text: str) -> tuple[Optional[float], Optional[int]]:
    """
    Parse weight and reps from natural speech for compound lifts.

    Examples:
        "20 kilos for 5 reps" -> (20.0, 5)
        "20 for 5" -> (20.0, 5)
        "20kg 5 reps" -> (20.0, 5)

    Returns:
        (weight, reps) or (None, None) if parsing fails
    """
    import re

    text = strip_hedging(text.lower())

    # Pattern: "X kilos for Y reps" or "X for Y"
    match = re.search(r"(\d+\.?\d*)\s*(?:kg|kilos?)?\s*(?:for|x)\s*(\d+)", text)
    if match:
        weight = float(match.group(1))
        reps = int(match.group(2))
        return (weight, reps)

    # Pattern: "X kg Y reps"
    match = re.search(r"(\d+\.?\d*)\s*(?:kg|kilos?)\s*(\d+)\s*(?:reps?)?", text)
    if match:
        weight = float(match.group(1))
        reps = int(match.group(2))
        return (weight, reps)

    return (None, None)


def parse_weight_value(text: str) -> Optional[float]:
    """
    Parse weight value from spoken text for workout tracking.

    Handles formats like:
        "30 kilos" -> 30.0
        "ready 25kg" -> 25.0
        "25" -> 25.0 (if plausible weight)
        "thirty kilos" -> 30.0

    Returns:
        Weight in kg or None if no valid weight found
    """
    text = strip_hedging(text.lower())

    # Try explicit weight+unit pattern first
    weight_match = re.search(r"(\d+\.?\d*)\s*(?:kg|kilos?|kilograms?)", text)
    if weight_match:
        try:
            weight = float(weight_match.group(1))
            if 1 <= weight <= 500:  # Sanity check
                return weight
        except ValueError:
            pass

    # Try to extract from weight_reps pattern
    weight, _ = parse_weight_reps(text)
    if weight and 1 <= weight <= 500:
        return weight

    # Try simple number extraction (only if plausible weight range)
    value = parse_spoken_number(text)
    if value is not None and 5 <= value <= 300:
        # Likely a weight value
        return value

    return None


from dataclasses import dataclass


@dataclass
class BodyComposition:
    """Body composition data from smart scale."""
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    muscle_mass_pct: Optional[float] = None
    water_pct: Optional[float] = None
    bone_mass_kg: Optional[float] = None
    visceral_fat: Optional[int] = None
    bmi: Optional[float] = None
    bmr: Optional[int] = None


def parse_body_composition(text: str) -> Optional[BodyComposition]:
    """
    Parse body composition from natural speech.

    Handles formats like:
        "83.2 kilos at 18 percent body fat" -> weight_kg=83.2, body_fat_pct=18
        "83 kg 18% fat 42% muscle" -> weight_kg=83, body_fat_pct=18, muscle_mass_pct=42
        "weighed in at 83.2" -> weight_kg=83.2
        "log weight 83.5 kilos, 18.5% fat, 42% muscle, 55% water, visceral 8"
        "83.2 kg 18.5% fat"

    Returns:
        BodyComposition dataclass or None if no valid weight found
    """
    text = strip_hedging(text.lower())
    result = BodyComposition()

    # Extract weight first (required)
    # Pattern: number followed by kg/kilos/kilograms (with optional space)
    weight_match = re.search(r"(\d+\.?\d*)\s*(?:kg|kilos?|kilograms?)", text)
    if weight_match:
        try:
            weight = float(weight_match.group(1))
            if 20 <= weight <= 300:
                result.weight_kg = weight
        except ValueError:
            pass

    # If no explicit unit, try "weighed in at X" pattern
    if result.weight_kg is None:
        weigh_match = re.search(r"weigh(?:ed)?\s+(?:in\s+)?(?:at\s+)?(\d+\.?\d*)", text)
        if weigh_match:
            try:
                weight = float(weigh_match.group(1))
                if 20 <= weight <= 300:
                    result.weight_kg = weight
            except ValueError:
                pass

    # If still no weight, try "X point Y" spoken format
    if result.weight_kg is None:
        point_match = re.search(r"(\d+)\s+point\s+(\d+)", text)
        if point_match:
            try:
                whole = int(point_match.group(1))
                decimal = int(point_match.group(2))
                weight = whole + decimal / (10 ** len(point_match.group(2)))
                if 20 <= weight <= 300:
                    result.weight_kg = weight
            except ValueError:
                pass

    # No weight found, return None
    if result.weight_kg is None:
        return None

    # Extract body fat percentage
    # Patterns: "18 percent body fat", "18% fat", "18.5% body fat", "at 18 percent"
    fat_patterns = [
        r"(\d+\.?\d*)\s*(?:percent|%)\s*(?:body\s*)?fat",
        r"(?:body\s*)?fat\s*(?:is|at|of)?\s*(\d+\.?\d*)\s*(?:percent|%)?",
        r"at\s+(\d+\.?\d*)\s*(?:percent|%)",  # "at 18 percent"
    ]
    for pattern in fat_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                fat = float(match.group(1))
                if 1 <= fat <= 70:
                    result.body_fat_pct = fat
                    break
            except ValueError:
                pass

    # Extract muscle mass percentage
    muscle_match = re.search(r"(\d+\.?\d*)\s*(?:percent|%)?\s*muscle", text)
    if muscle_match:
        try:
            muscle = float(muscle_match.group(1))
            if 10 <= muscle <= 70:
                result.muscle_mass_pct = muscle
        except ValueError:
            pass

    # Extract water percentage
    water_match = re.search(r"(\d+\.?\d*)\s*(?:percent|%)?\s*water", text)
    if water_match:
        try:
            water = float(water_match.group(1))
            if 30 <= water <= 80:
                result.water_pct = water
        except ValueError:
            pass

    # Extract bone mass (kg)
    bone_match = re.search(r"bone\s*(?:mass)?\s*(\d+\.?\d*)\s*(?:kg|kilos?)?", text)
    if bone_match:
        try:
            bone = float(bone_match.group(1))
            if 1 <= bone <= 10:
                result.bone_mass_kg = bone
        except ValueError:
            pass

    # Extract visceral fat (integer 1-59)
    visceral_match = re.search(r"visceral\s*(?:fat)?\s*(\d+)", text)
    if visceral_match:
        try:
            visceral = int(visceral_match.group(1))
            if 1 <= visceral <= 59:
                result.visceral_fat = visceral
        except ValueError:
            pass

    # Extract BMI
    bmi_match = re.search(r"bmi\s*(?:is|of|at)?\s*(\d+\.?\d*)", text)
    if bmi_match:
        try:
            bmi = float(bmi_match.group(1))
            if 10 <= bmi <= 60:
                result.bmi = bmi
        except ValueError:
            pass

    # Extract BMR
    bmr_match = re.search(r"bmr\s*(?:is|of|at)?\s*(\d+)", text)
    if bmr_match:
        try:
            bmr = int(bmr_match.group(1))
            if 800 <= bmr <= 4000:
                result.bmr = bmr
        except ValueError:
            pass

    return result


# Export main functions
__all__ = [
    "parse_spoken_number",
    "parse_boolean",
    "parse_categorical",
    "parse_fms_score",
    "parse_duration",
    "parse_blood_pressure",
    "parse_weight_reps",
    "parse_weight_value",
    "parse_body_composition",
    "BodyComposition",
    "format_echo",
]
