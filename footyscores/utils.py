from typing import Any, List

from .constants import MISSING_MATCH_STATUS, MISSING_SCORE, MISSING_STRING


def is_record(value: Any) -> bool:
    return isinstance(value, dict)


def as_array(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def as_string(value: Any, fallback: str = "") -> str:
    return value if isinstance(value, str) else fallback


def as_number(value: Any, fallback: int = MISSING_SCORE) -> int:
    if isinstance(value, bool):
        return fallback
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            try:
                return int(stripped)
            except ValueError:
                return fallback
    return fallback


def normalize_status(value: str) -> str:
    status = value.strip().upper()
    if status in {"FINISHED", "OFFICIAL"}:
        return "FT"
    if status == "SCHEDULED":
        return MISSING_MATCH_STATUS
    if status == "HALF_TIME":
        return "HT"
    return status or MISSING_MATCH_STATUS


def parse_venue_city(description: str) -> str:
    parts = [part.strip() for part in description.split(",") if part.strip()]
    return parts[-1] if parts else MISSING_STRING
