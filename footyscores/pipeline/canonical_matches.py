from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Mapping, Optional

from ..constants import (
    DEFAULT_MATCH_REQUEST_CONCURRENCY,
    DEFAULT_TIMEOUT_SECONDS,
    MISSING_MATCH_STATUS,
    MISSING_STRING,
)
from ..models import (
    CanonicalMatch,
    CanonicalTeam,
    CanonicalTeamLineup,
    EventGameSummary,
    ParsedMatchDetail,
    ScheduledMatch,
    ScheduledTeam,
)
from ..parsers.olympics_parsers import (
    build_round_lookup,
    create_empty_match_detail,
    parse_event_game_summaries,
    parse_football_schedule,
    parse_match_detail,
)
from ..source.concurrency import map_with_concurrency
from ..source.olympics_data import (
    retrieve_event_games,
    retrieve_event_phases,
    retrieve_football_event_units,
    retrieve_football_schedule,
    retrieve_match_results,
)


def create_empty_lineup(team_name: str) -> CanonicalTeamLineup:
    return CanonicalTeamLineup(
        team=team_name,
        formation=MISSING_STRING,
        coach=MISSING_STRING,
        starting_xi=[],
        bench=[],
    )


def resolve_team(team: ScheduledTeam, detail: ParsedMatchDetail) -> CanonicalTeam:
    lineup = detail.lineups.get(team.code) or create_empty_lineup(team.name)
    return CanonicalTeam(code=team.code, name=team.name, lineup=lineup)


def resolve_detail(
    detail: ParsedMatchDetail,
    summary: Optional[EventGameSummary],
    scheduled_status: str,
) -> ParsedMatchDetail:
    if detail.status != MISSING_MATCH_STATUS or summary is None:
        return ParsedMatchDetail(
            status=scheduled_status if detail.status == MISSING_MATCH_STATUS else detail.status,
            score_home=detail.score_home,
            score_away=detail.score_away,
            score_half_time_home=detail.score_half_time_home,
            score_half_time_away=detail.score_half_time_away,
            scorers=detail.scorers,
            lineups=detail.lineups,
        )
    return ParsedMatchDetail(
        status=scheduled_status if summary.status == MISSING_MATCH_STATUS else summary.status,
        score_home=summary.score_home,
        score_away=summary.score_away,
        score_half_time_home=detail.score_half_time_home,
        score_half_time_away=detail.score_half_time_away,
        scorers=detail.scorers,
        lineups=detail.lineups,
    )


def build_canonical_matches(
    schedule_matches: List[ScheduledMatch],
    match_result_payloads: Mapping[str, Any],
    event_units_payload: Any,
    phase_payloads: List[Any],
    event_games_payloads: List[Any],
) -> List[CanonicalMatch]:
    round_lookup = build_round_lookup(phase_payloads, event_units_payload, event_games_payloads)
    summaries = parse_event_game_summaries(event_games_payloads)

    canonical_matches: List[CanonicalMatch] = []
    for scheduled_match in schedule_matches:
        payload = match_result_payloads.get(scheduled_match.match_code)
        parsed_detail = (
            create_empty_match_detail() if payload is None else parse_match_detail(payload)
        )
        summary = summaries.get(scheduled_match.match_code)
        detail = resolve_detail(parsed_detail, summary, scheduled_match.status)

        canonical_matches.append(
            CanonicalMatch(
                match_code=scheduled_match.match_code,
                event_code=scheduled_match.event_code,
                kickoff=scheduled_match.kickoff,
                status=detail.status,
                competition_name="Olympic Football Tournament",
                competition_season="2024",
                competition_round=round_lookup.get(scheduled_match.match_code)
                or (summary.round_name if summary else MISSING_STRING),
                venue_name=scheduled_match.venue_name,
                venue_city=scheduled_match.venue_city,
                home=resolve_team(scheduled_match.home, detail),
                away=resolve_team(scheduled_match.away, detail),
                score_home=detail.score_home,
                score_away=detail.score_away,
                score_half_time_home=detail.score_half_time_home,
                score_half_time_away=detail.score_half_time_away,
                scorers=detail.scorers,
            )
        )
    return canonical_matches


def generate_canonical_matches(
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    concurrency: int = DEFAULT_MATCH_REQUEST_CONCURRENCY,
) -> List[CanonicalMatch]:
    schedule_payload = retrieve_football_schedule(timeout_seconds)
    schedule_matches = parse_football_schedule(schedule_payload)
    event_codes = list(dict.fromkeys(match.event_code for match in schedule_matches))
    match_codes = [match.match_code for match in schedule_matches]

    with ThreadPoolExecutor(max_workers=4) as executor:
        event_units_future = executor.submit(retrieve_football_event_units, timeout_seconds)
        event_games_future = executor.submit(
            map_with_concurrency,
            event_codes,
            max(1, min(6, len(event_codes))),
            lambda event_code: retrieve_event_games(event_code, timeout_seconds),
        )
        phases_future = executor.submit(
            map_with_concurrency,
            event_codes,
            max(1, min(6, len(event_codes))),
            lambda event_code: retrieve_event_phases(event_code, timeout_seconds),
        )
        match_results_future = executor.submit(
            retrieve_match_results, match_codes, timeout_seconds, concurrency
        )

        event_units_payload = event_units_future.result()
        event_games_payloads = event_games_future.result()
        phase_payloads = phases_future.result()
        match_result_payloads = match_results_future.result()

    return build_canonical_matches(
        schedule_matches=schedule_matches,
        match_result_payloads=match_result_payloads,
        event_units_payload=event_units_payload,
        phase_payloads=phase_payloads,
        event_games_payloads=event_games_payloads,
    )
