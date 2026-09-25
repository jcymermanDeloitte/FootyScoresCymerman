from typing import Any, Dict, List

from ..constants import DEFAULT_MATCH_REQUEST_CONCURRENCY, DEFAULT_TIMEOUT_SECONDS
from ..errors import MatchNotFoundError
from ..models import CanonicalMatch
from ..transformers.to_endpoint import to_endpoint
from .canonical_matches import generate_canonical_matches


def sort_canonical_matches(matches: List[CanonicalMatch]) -> List[CanonicalMatch]:
    return sorted(
        matches,
        key=lambda match: (
            match.kickoff,
            match.home.name,
            match.away.name,
            match.match_code,
        ),
    )


def generate_matches(
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    concurrency: int = DEFAULT_MATCH_REQUEST_CONCURRENCY,
) -> List[CanonicalMatch]:
    return sort_canonical_matches(generate_canonical_matches(timeout_seconds, concurrency))


def generate_match_endpoint(
    match_code: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    concurrency: int = DEFAULT_MATCH_REQUEST_CONCURRENCY,
) -> Dict[str, Any]:
    normalized_match_code = match_code.strip()
    match = next(
        (
            candidate
            for candidate in generate_matches(timeout_seconds, concurrency)
            if candidate.match_code == normalized_match_code
        ),
        None,
    )
    if not match:
        raise MatchNotFoundError(normalized_match_code)
    return to_endpoint(match)
