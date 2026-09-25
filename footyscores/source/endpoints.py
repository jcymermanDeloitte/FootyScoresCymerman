from urllib.parse import quote

from ..constants import OLYMPICS_DATA_BASE_URL


def build_data_url(file_name: str) -> str:
    return f"{OLYMPICS_DATA_BASE_URL}/{file_name}"


def require_code(code: str, kind: str) -> str:
    normalized = code.strip()
    if not normalized:
        raise TypeError(f"{kind} code must not be empty.")
    return normalized


def olympics_football_start_list_url() -> str:
    return build_data_url("SCH_StartList~comp=OG2024~disc=FBL~lang=ENG.json")


def olympics_football_event_units_url() -> str:
    return build_data_url("GLO_EventUnits~comp=OG2024~disc=FBL~lang=ENG.json")


def olympics_event_games_url(event_code: str) -> str:
    code = quote(require_code(event_code, "event"))
    return build_data_url(f"GLO_EventGames~comp=OG2024~event={code}~lang=ENG.json")


def olympics_event_phases_url(event_code: str) -> str:
    code = quote(require_code(event_code, "event"))
    return build_data_url(f"SEL_Phases~comp=OG2024~lang=ENG~event={code}.json")


def olympics_result_by_match_url(match_code: str) -> str:
    code = quote(require_code(match_code, "match"))
    return build_data_url(
        f"RES_ByRSC_H2H~comp=OG2024~disc=FBL~rscResult={code}~lang=ENG.json"
    )
