from typing import Any, Dict

from ..constants import MISSING_STRING
from ..models import CanonicalMatch, CanonicalPlayer, CanonicalScorer, CanonicalTeamLineup


def resolve_scorer_team(match: CanonicalMatch, scorer: CanonicalScorer) -> str:
    if scorer.team_code == match.home.code:
        return match.home.name
    if scorer.team_code == match.away.code:
        return match.away.name
    return MISSING_STRING


def player_to_dict(player: CanonicalPlayer) -> Dict[str, Any]:
    return {
        "name": player.name,
        "number": player.number,
        "position": player.position,
    }


def lineup_to_dict(lineup: CanonicalTeamLineup) -> Dict[str, Any]:
    return {
        "team": lineup.team,
        "formation": lineup.formation,
        "coach": lineup.coach,
        "startingXI": [player_to_dict(player) for player in lineup.starting_xi],
        "bench": [player_to_dict(player) for player in lineup.bench],
    }


def to_endpoint(match: CanonicalMatch) -> Dict[str, Any]:
    scorers = []
    for scorer in match.scorers:
        scorer_output = {
            "team": resolve_scorer_team(match, scorer),
            "player": scorer.player,
            "minute": scorer.minute,
            "type": scorer.goal_type,
        }
        if scorer.assist:
            scorer_output["assist"] = scorer.assist
        scorers.append(scorer_output)

    return {
        "competition": {
            "name": match.competition_name,
            "season": match.competition_season,
            "round": match.competition_round,
        },
        "venue": {
            "name": match.venue_name,
            "city": match.venue_city,
        },
        "kickoff": match.kickoff,
        "status": match.status,
        "teams": {
            "home": match.home.name,
            "away": match.away.name,
        },
        "score": {
            "home": match.score_home,
            "away": match.score_away,
            "halfTime": {
                "home": match.score_half_time_home,
                "away": match.score_half_time_away,
            },
        },
        "scorers": scorers,
        "lineups": {
            "home": lineup_to_dict(match.home.lineup),
            "away": lineup_to_dict(match.away.lineup),
        },
    }
