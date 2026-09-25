from typing import List

from ..models import CanonicalMatch


def format_match_list(matches: List[CanonicalMatch]) -> str:
    return "\n".join(
        f"{match.match_code} | {match.kickoff} | {match.home.name} vs {match.away.name}"
        for match in matches
    )
