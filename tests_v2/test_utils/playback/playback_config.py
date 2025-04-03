import re
from typing import Any, Callable


class PlaybackConfiguration:
    """Configuration for playback tests.

    This class is used to configure the playback tests.
    It allows you to specify which properties to ignore, which properties to replace,
    and custom matching for properties.

    Attributes:
        ignore_properties (list[str | Callable[[Any], bool]]):
            Indicates which properties to ignore.
            Can be a property path or a callable that takes a value and returns a boolean.
            Property paths are JSON path encoded e.g. "params.serverInfos.0.serverVersion".
            The property paths here can also be wildcards e.g. ".*.serverVersion", which will
            match any property with the name "serverVersion" at any level.
        replace_properties (list[str]): List of properties to replace.
            Takes a full property path e.g. "params.connectionId". The value of this property
            will be marked as a replacement into the replace_properties attribute.
            Subsiquent messages will be modified to use the replacement value if their
            property matches the property path and the value matches the original value.
            This allows non-deterministic values, e.g. UUIDs, to be replaced with the correct
            value during playback.
        match_properties (dict[str, Callable[[Any, Any], bool]]):
            Dictionary of properties with custom matching functions.
            The key is the property path and the value is a callable that takes two values,
            the recorded value and the playback value, and returns True if they match.
        ignore_server_notification_methods (list[str] | None):
            List of server notification methods to ignore.
            This is useful for notifications that are not relevant to the test.
            Defaults to None, which means all notifications are considered.
        ignore_responses (list[str] | None):
            List of responses to ignore.
            This is useful for responses that are not relevant to the test.
            Defaults to None, which means all responses are considered.
        timeout (float): Timeout for the tests.
            Defaults to 2.0 seconds.
    """

    def __init__(
        self,
        ignore_properties: list[str | Callable[[Any], bool]],
        replace_properties: list[str],
        match_properties: dict[str, Callable[[Any, Any], bool]],
        ignore_server_notification_methods: list[str] | None = None,
        ignore_responses: list[str] | None = None,
        timeout: float = 2.0,
    ) -> None:
        self.timeout = timeout
        self.ignore_properties = ignore_properties
        self.match_properties = match_properties
        self.replace_properties: dict[str, list[tuple[Any, Any]]] = {
            k: [] for k in replace_properties
        }
        self.ignore_server_notification_methods = ignore_server_notification_methods or []
        self.ignore_responses = ignore_responses or []

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
            ignore_server_notification_methods=[],
            ignore_responses=[],
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
