from typing import Optional


class SchedulePayloadError(Exception):
    pass


class MatchNotFoundError(Exception):
    def __init__(self, match_code: str):
        super().__init__(f'No generated match exists for match code "{match_code}".')


class OlympicsFetchError(Exception):
    def __init__(self, message: str, url: str, cause: Optional[BaseException] = None):
        super().__init__(message)
        self.url = url
        self.__cause__ = cause


class OlympicsTimeoutError(OlympicsFetchError):
    pass


class OlympicsHttpError(OlympicsFetchError):
    def __init__(self, url: str, status: int, reason: str):
        super().__init__(f"HTTP {status} {reason}: {url}", url)
        self.status = status
        self.reason = reason


class OlympicsInvalidJsonError(OlympicsFetchError):
    pass
