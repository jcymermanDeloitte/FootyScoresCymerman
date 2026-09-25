from typing import Any, Dict, List

from ..constants import DEFAULT_MATCH_REQUEST_CONCURRENCY, DEFAULT_TIMEOUT_SECONDS
from .concurrency import map_with_concurrency
from .endpoints import (
    olympics_event_games_url,
    olympics_event_phases_url,
    olympics_football_event_units_url,
    olympics_football_start_list_url,
    olympics_result_by_match_url,
)
from .http_client import fetch_olympics_json


def retrieve_football_schedule(timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> Any:
    return fetch_olympics_json(olympics_football_start_list_url(), timeout_seconds)


def retrieve_football_event_units(timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> Any:
    return fetch_olympics_json(olympics_football_event_units_url(), timeout_seconds)


def retrieve_event_games(event_code: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> Any:
    return fetch_olympics_json(olympics_event_games_url(event_code), timeout_seconds)


def retrieve_event_phases(event_code: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> Any:
    return fetch_olympics_json(olympics_event_phases_url(event_code), timeout_seconds)


def retrieve_match_result(match_code: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> Any:
    return fetch_olympics_json(olympics_result_by_match_url(match_code), timeout_seconds)


def retrieve_match_results(
    match_codes: List[str],
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    concurrency: int = DEFAULT_MATCH_REQUEST_CONCURRENCY,
) -> Dict[str, Any]:
    unique_match_codes = list(dict.fromkeys(match_codes))
    payloads = map_with_concurrency(
        unique_match_codes,
        concurrency,
        lambda match_code: retrieve_match_result(match_code, timeout_seconds),
    )
    return {match_code: payloads[index] for index, match_code in enumerate(unique_match_codes)}
