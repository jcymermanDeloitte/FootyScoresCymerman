import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..constants import DEFAULT_TIMEOUT_SECONDS, OLYMPICS_REQUEST_HEADERS
from ..errors import (
    OlympicsFetchError,
    OlympicsHttpError,
    OlympicsInvalidJsonError,
    OlympicsTimeoutError,
)


def validate_timeout(timeout_seconds: int) -> None:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be a positive integer.")


def fetch_olympics_json(url: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> Any:
    validate_timeout(timeout_seconds)
    request = Request(url=url, headers=OLYMPICS_REQUEST_HEADERS)

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status = getattr(response, "status", 200)
            reason = getattr(response, "reason", "OK")
            if status < 200 or status >= 300:
                raise OlympicsHttpError(url, status, str(reason))
            try:
                return json.loads(response.read().decode("utf-8"))
            except json.JSONDecodeError as error:
                raise OlympicsInvalidJsonError(f"Invalid JSON response: {url}", url, error)
    except HTTPError as error:
        raise OlympicsHttpError(url, error.code, error.reason) from error
    except URLError as error:
        reason = getattr(error, "reason", "")
        if isinstance(reason, TimeoutError):
            raise OlympicsTimeoutError(
                f"Request timed out after {timeout_seconds * 1000}ms: {url}",
                url,
                error,
            ) from error
        raise OlympicsFetchError(f"Network request failed: {url}", url, error) from error
    except TimeoutError as error:
        raise OlympicsTimeoutError(
            f"Request timed out after {timeout_seconds * 1000}ms: {url}",
            url,
            error,
        ) from error
