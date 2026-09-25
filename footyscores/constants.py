MISSING_STRING = "Unknown"
MISSING_MATCH_STATUS = "NS"
MISSING_SCORE = 0
EVENT_CODE_LENGTH = 22
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_MATCH_REQUEST_CONCURRENCY = 8

OLYMPICS_DATA_BASE_URL = "https://stacy.olympics.com/OG2024/data"
SCHEDULE_REFERER = "https://stacy.olympics.com/en/paris-2024/competition-schedule"
OLYMPICS_REQUEST_HEADERS = {
    "Accept": "application/json",
    "Referer": SCHEDULE_REFERER,
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
}

KNOWN_POSITIONS = {
    "GK",
    "RB",
    "LB",
    "CB",
    "RWB",
    "LWB",
    "DM",
    "CM",
    "AM",
    "RW",
    "LW",
    "ST",
    "FW",
    "DF",
    "MF",
}
