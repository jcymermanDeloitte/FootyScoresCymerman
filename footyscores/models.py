from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ScheduledTeam:
    code: str
    name: str


@dataclass(frozen=True)
class ScheduledMatch:
    match_code: str
    event_code: str
    kickoff: str
    status: str
    venue_name: str
    venue_city: str
    home: ScheduledTeam
    away: ScheduledTeam


@dataclass(frozen=True)
class CanonicalPlayer:
    name: str
    number: int
    position: str


@dataclass(frozen=True)
class CanonicalTeamLineup:
    team: str
    formation: str
    coach: str
    starting_xi: List[CanonicalPlayer]
    bench: List[CanonicalPlayer]


@dataclass(frozen=True)
class CanonicalTeam:
    code: str
    name: str
    lineup: CanonicalTeamLineup


@dataclass(frozen=True)
class CanonicalScorer:
    team_code: str
    player: str
    minute: int
    goal_type: str
    assist: Optional[str] = None


@dataclass(frozen=True)
class ParsedMatchDetail:
    status: str
    score_home: int
    score_away: int
    score_half_time_home: int
    score_half_time_away: int
    scorers: List[CanonicalScorer]
    lineups: Dict[str, CanonicalTeamLineup]


@dataclass(frozen=True)
class EventGameSummary:
    status: str
    score_home: int
    score_away: int
    round_name: str


@dataclass(frozen=True)
class CanonicalMatch:
    match_code: str
    event_code: str
    kickoff: str
    status: str
    competition_name: str
    competition_season: str
    competition_round: str
    venue_name: str
    venue_city: str
    home: CanonicalTeam
    away: CanonicalTeam
    score_home: int
    score_away: int
    score_half_time_home: int
    score_half_time_away: int
    scorers: List[CanonicalScorer]
