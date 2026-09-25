import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional

from ..constants import (
    EVENT_CODE_LENGTH,
    KNOWN_POSITIONS,
    MISSING_MATCH_STATUS,
    MISSING_SCORE,
    MISSING_STRING,
)
from ..errors import SchedulePayloadError
from ..models import (
    CanonicalPlayer,
    CanonicalScorer,
    CanonicalTeamLineup,
    EventGameSummary,
    ParsedMatchDetail,
    ScheduledMatch,
    ScheduledTeam,
)
from ..utils import as_array, as_number, as_string, is_record, normalize_status, parse_venue_city


def parse_scheduled_team(value: Any, index: int) -> ScheduledTeam:
    if not is_record(value):
        raise SchedulePayloadError(f"Schedule entry is missing team {index + 1}.")
    participant = value.get("participant") if is_record(value.get("participant")) else {}
    code = as_string(value.get("teamCode"), as_string(participant.get("code"))).strip()
    name = as_string(participant.get("name"), MISSING_STRING).strip() or MISSING_STRING
    if not code:
        raise SchedulePayloadError(f"Schedule entry team {index + 1} has no code.")
    return ScheduledTeam(code=code, name=name)


def sort_by_order(entry: Any) -> int:
    if not is_record(entry):
        return sys.maxsize
    return as_number(entry.get("startOrder"), as_number(entry.get("sortOrder"), sys.maxsize))


def parse_football_schedule(payload: Any) -> List[ScheduledMatch]:
    if not is_record(payload) or not isinstance(payload.get("schedules"), list):
        raise SchedulePayloadError("Schedule payload does not contain a schedules array.")

    matches: List[ScheduledMatch] = []
    seen_match_codes: set[str] = set()

    for index, value in enumerate(payload["schedules"]):
        if not is_record(value):
            raise SchedulePayloadError(f"Schedule entry {index} is not an object.")
        match_code = as_string(value.get("code")).strip()
        if not match_code.startswith("FBL") or match_code in seen_match_codes:
            continue

        start_entries = sorted(as_array(value.get("start")), key=sort_by_order)
        if len(start_entries) < 2:
            continue

        kickoff = as_string(value.get("startDate")).strip()
        if len(match_code) < EVENT_CODE_LENGTH or not kickoff:
            raise SchedulePayloadError(
                f"Schedule entry {index} is missing required match data."
            )

        status = value.get("status") if is_record(value.get("status")) else {}
        venue = value.get("venue") if is_record(value.get("venue")) else {}
        location = value.get("location") if is_record(value.get("location")) else {}

        seen_match_codes.add(match_code)
        matches.append(
            ScheduledMatch(
                match_code=match_code,
                event_code=match_code[:EVENT_CODE_LENGTH],
                kickoff=kickoff,
                status=normalize_status(as_string(status.get("code"))),
                venue_name=as_string(venue.get("description"), MISSING_STRING).strip()
                or MISSING_STRING,
                venue_city=parse_venue_city(as_string(location.get("description"))),
                home=parse_scheduled_team(start_entries[0], 0),
                away=parse_scheduled_team(start_entries[1], 1),
            )
        )

    return matches


def extract_entry_value(entries: List[Any], code: str) -> str:
    for value in entries:
        if is_record(value) and as_string(value.get("eue_code")) == code:
            return as_string(value.get("eue_value"))
    return ""


def extract_position(entries: List[Any]) -> str:
    positions = [
        as_string(value.get("eue_value"))
        for value in entries
        if is_record(value)
        and as_string(value.get("eue_code")) == "POSITION"
        and as_string(value.get("eue_value"))
    ]
    for position in positions:
        if position in KNOWN_POSITIONS:
            return position
    return positions[0] if positions else MISSING_STRING


def extract_coach(value: Any) -> str:
    coaches = as_array(value)
    head_coach = None
    for entry in coaches:
        if not is_record(entry):
            continue
        role = entry.get("function") if is_record(entry.get("function")) else {}
        if as_string(role.get("functionCode")) == "COACH":
            head_coach = entry
            break
    coach_entry = head_coach or next((entry for entry in coaches if is_record(entry)), None)
    if not is_record(coach_entry):
        return MISSING_STRING
    coach = coach_entry.get("coach") if is_record(coach_entry.get("coach")) else {}
    return as_string(coach.get("name"), MISSING_STRING).strip() or MISSING_STRING


def parse_lineup_player(value: Any) -> Optional[Dict[str, Any]]:
    if not is_record(value):
        return None
    athlete = value.get("athlete") if is_record(value.get("athlete")) else {}
    entries = as_array(value.get("eventUnitEntries"))
    return {
        "player": CanonicalPlayer(
            name=as_string(athlete.get("name"), MISSING_STRING).strip() or MISSING_STRING,
            number=as_number(value.get("bib")),
            position=extract_position(entries),
        ),
        "is_starter": extract_entry_value(entries, "STARTER") == "Y",
        "order": as_number(value.get("startSortOrder"), as_number(value.get("order"), sys.maxsize)),
        "participant_code": as_string(value.get("participantCode")),
    }


def parse_team_lineup(value: Any) -> Optional[Dict[str, Any]]:
    if not is_record(value):
        return None
    participant = value.get("participant") if is_record(value.get("participant")) else {}
    team_code = as_string(value.get("teamCode"), as_string(participant.get("code"))).strip()
    if not team_code:
        return None

    parsed_players = [
        player
        for player in (parse_lineup_player(v) for v in as_array(value.get("teamAthletes")))
        if player is not None
    ]
    parsed_players.sort(key=lambda player: player["order"])

    athlete_names: Dict[str, str] = {}
    for player in parsed_players:
        participant_code = as_string(player["participant_code"])
        if participant_code:
            athlete_names[participant_code] = player["player"].name

    lineup = CanonicalTeamLineup(
        team=as_string(participant.get("name"), MISSING_STRING).strip() or MISSING_STRING,
        formation=extract_entry_value(as_array(value.get("eventUnitEntries")), "FORMATION")
        or MISSING_STRING,
        coach=extract_coach(value.get("teamCoaches")),
        starting_xi=[player["player"] for player in parsed_players if player["is_starter"]],
        bench=[player["player"] for player in parsed_players if not player["is_starter"]],
    )

    return {"team_code": team_code, "lineup": lineup, "athlete_names": athlete_names}


def extract_minute(value: str) -> int:
    normalized = "".join(value.split())
    if "'+" in normalized:
        prefix, suffix = normalized.split("'+", 1)
        try:
            base = int(prefix)
            added = ""
            for character in suffix:
                if character.isdigit():
                    added += character
                else:
                    break
            return base + (int(added) if added else 0)
        except ValueError:
            return MISSING_SCORE
    if "'" in normalized:
        minute = normalized.split("'", 1)[0]
        try:
            return int(minute)
        except ValueError:
            return MISSING_SCORE
    return MISSING_SCORE


def infer_goal_type(action: str, comment: str) -> str:
    description = f"{action} {comment}".upper()
    if "PEN" in description:
        return "penalty"
    if "HEAD" in description:
        return "header"
    return "open_play"


def parse_scorers(value: Any, athlete_names: Mapping[str, str]) -> List[CanonicalScorer]:
    scorers: List[CanonicalScorer] = []
    for period in as_array(value):
        if not is_record(period):
            continue
        for action in as_array(period.get("actions")):
            if not is_record(action) or as_string(action.get("pbpa_Result")) != "GOAL":
                continue
            competitors = [item for item in as_array(action.get("competitors")) if is_record(item)]
            competitor = competitors[0] if competitors else None
            if not competitor:
                continue

            athletes = [item for item in as_array(competitor.get("athletes")) if is_record(item)]
            scorer = next(
                (athlete for athlete in athletes if as_string(athlete.get("pbpat_role")) == "SCR"),
                None,
            )
            assister = next(
                (
                    athlete
                    for athlete in athletes
                    if as_string(athlete.get("pbpat_role")) == "ASSIST"
                ),
                None,
            )
            scorer_code = as_string(scorer.get("pbpat_code")) if is_record(scorer) else ""
            assist_code = as_string(assister.get("pbpat_code")) if is_record(assister) else ""
            team_code = as_string(competitor.get("pbpc_code"))

            if not team_code:
                continue

            assist_name = athlete_names.get(assist_code)
            scorers.append(
                CanonicalScorer(
                    team_code=team_code,
                    player=athlete_names.get(scorer_code, MISSING_STRING),
                    minute=extract_minute(as_string(action.get("pbpa_When"))),
                    assist=assist_name if assist_name else None,
                    goal_type=infer_goal_type(
                        as_string(action.get("pbpa_Action")),
                        as_string(action.get("pbpa_Comment")),
                    ),
                )
            )

    unique: List[CanonicalScorer] = []
    seen: set[str] = set()
    for scorer in scorers:
        key = f"{scorer.team_code}|{scorer.player}|{scorer.minute}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(scorer)
    unique.sort(key=lambda scorer: scorer.minute)
    return unique


def extract_result_status(results: Dict[str, Any]) -> str:
    for info in as_array(results.get("extendedInfos")):
        if is_record(info) and as_string(info.get("ei_code")) == "PERIOD":
            return normalize_status(as_string(info.get("ei_value")))
    status = results.get("status") if is_record(results.get("status")) else {}
    return normalize_status(as_string(status.get("code")))


def parse_score(periods: Any) -> Dict[str, int]:
    values = [period for period in as_array(periods) if is_record(period)]
    total = next((period for period in values if as_string(period.get("p_code")) == "TOT"), {})
    half_time = next((period for period in values if as_string(period.get("p_code")) == "H1"), {})
    total_home = total.get("home") if is_record(total.get("home")) else {}
    total_away = total.get("away") if is_record(total.get("away")) else {}
    half_time_home = half_time.get("home") if is_record(half_time.get("home")) else {}
    half_time_away = half_time.get("away") if is_record(half_time.get("away")) else {}
    return {
        "home": as_number(total_home.get("score")),
        "away": as_number(total_away.get("score")),
        "half_time_home": as_number(half_time_home.get("score")),
        "half_time_away": as_number(half_time_away.get("score")),
    }


def create_empty_match_detail() -> ParsedMatchDetail:
    return ParsedMatchDetail(
        status=MISSING_MATCH_STATUS,
        score_home=MISSING_SCORE,
        score_away=MISSING_SCORE,
        score_half_time_home=MISSING_SCORE,
        score_half_time_away=MISSING_SCORE,
        scorers=[],
        lineups={},
    )


def parse_match_detail(payload: Any) -> ParsedMatchDetail:
    if not is_record(payload) or not is_record(payload.get("results")):
        return create_empty_match_detail()

    results = payload["results"]
    parsed_lineups = [
        lineup
        for lineup in (parse_team_lineup(value) for value in as_array(results.get("items")))
        if lineup is not None
    ]

    athlete_names: Dict[str, str] = {}
    lineups: Dict[str, CanonicalTeamLineup] = {}
    for lineup_data in parsed_lineups:
        lineups[lineup_data["team_code"]] = lineup_data["lineup"]
        for code, name in lineup_data["athlete_names"].items():
            athlete_names[code] = name

    score = parse_score(results.get("periods"))
    return ParsedMatchDetail(
        status=extract_result_status(results),
        score_home=score["home"],
        score_away=score["away"],
        score_half_time_home=score["half_time_home"],
        score_half_time_away=score["half_time_away"],
        scorers=parse_scorers(results.get("playByPlay"), athlete_names),
        lineups=lineups,
    )


def extract_round(value: Dict[str, Any], fallback: str = MISSING_STRING) -> str:
    return (
        as_string(value.get("shortDescription")).strip()
        or as_string(value.get("description")).strip()
        or fallback
    )


def add_rounds_from_phases(payload: Any, rounds: Dict[str, str]) -> None:
    if not is_record(payload) or not is_record(payload.get("event")):
        return
    for phase in as_array(payload["event"].get("phases")):
        if not is_record(phase):
            continue
        phase_round = extract_round(phase)
        for unit in as_array(phase.get("units")):
            if not is_record(unit):
                continue
            match_code = as_string(unit.get("code"))
            if match_code and match_code not in rounds:
                rounds[match_code] = extract_round(unit, phase_round)


def build_round_lookup(
    phase_payloads: Iterable[Any],
    event_units_payload: Any,
    event_games_payloads: Iterable[Any],
) -> Dict[str, str]:
    rounds: Dict[str, str] = {}
    for payload in phase_payloads:
        add_rounds_from_phases(payload, rounds)
    if is_record(event_units_payload):
        for unit in as_array(event_units_payload.get("eventUnits")):
            if not is_record(unit) or as_string(unit.get("type")) != "HTEAM":
                continue
            match_code = as_string(unit.get("code"))
            if match_code and match_code not in rounds:
                rounds[match_code] = extract_round(unit)
    for payload in event_games_payloads:
        add_rounds_from_phases(payload, rounds)
    return rounds


def parse_event_game_summaries(payloads: Iterable[Any]) -> Dict[str, EventGameSummary]:
    summaries: Dict[str, EventGameSummary] = {}
    for payload in payloads:
        if not is_record(payload) or not is_record(payload.get("event")):
            continue
        for phase in as_array(payload["event"].get("phases")):
            if not is_record(phase):
                continue
            phase_round = extract_round(phase)
            for unit in as_array(phase.get("units")):
                if not is_record(unit):
                    continue
                match_code = as_string(unit.get("code"))
                schedule = unit.get("schedule") if is_record(unit.get("schedule")) else {}
                result = schedule.get("result") if is_record(schedule.get("result")) else {}
                items = [item for item in as_array(result.get("items")) if is_record(item)]
                home = next((item for item in items if as_string(item.get("startOrder")) == "1"), {})
                away = next((item for item in items if as_string(item.get("startOrder")) == "2"), {})
                extended_status = extract_result_status({"extendedInfos": result.get("extendedInfos")})
                status_record = schedule.get("status") if is_record(schedule.get("status")) else {}
                if not match_code:
                    continue
                status = (
                    normalize_status(as_string(status_record.get("code")))
                    if extended_status == MISSING_MATCH_STATUS
                    else extended_status
                )
                summaries[match_code] = EventGameSummary(
                    status=status,
                    score_home=as_number(home.get("resultData")),
                    score_away=as_number(away.get("resultData")),
                    round_name=extract_round(unit, phase_round),
                )
    return summaries
