import re
from typing import Any, Callable


class PlaybackConfiguration:
    def __init__(
        self,
        ignore_properties: list[str | Callable[[Any], bool]],
        replace_properties: list[str],
        match_properties: dict[str, Callable[[Any, Any], bool]],
        timeout: float = 2.0,
    ) -> None:
        self.timeout = timeout
        self.ignore_properties = ignore_properties
        self.match_properties = match_properties
        self.replace_properties: dict[str, list[tuple[Any, Any]]] = {
            k: [] for k in replace_properties
        }

    @classmethod
    def default(cls) -> "PlaybackConfiguration":
        return cls(
            ignore_properties=[
                "params.serverInfo.serverVersion",
                "*.time",
                is_timestamp,
                is_tempfile,
            ],
            replace_properties=["params.connectionId"],
            match_properties={},
        )


def is_timestamp(value: Any) -> bool:
    """Check if the value is a timestamp string.

    E.g. "2025-02-24T13:04:39.349672" or "0:00:00.004687"
    """
    if not isinstance(value, str):
        return False
    # Use regex
    time_regex = r".*:\d{2}:\d{2}\.\d{6}$"
    return bool(re.match(time_regex, value))


def is_tempfile(value: Any) -> bool:
    """Check if the value is a tempfile string.

    E.g. "/tmp/xxxxxx"
    """
    if not isinstance(value, str):
        return False
    # Use regex
    time_regex = r"^file://.*/tmp[^\.]*.sql$"
    return bool(re.match(time_regex, value))
