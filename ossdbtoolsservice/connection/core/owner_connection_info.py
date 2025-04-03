from dataclasses import dataclass

from ossdbtoolsservice.connection.contracts.common import (
    ConnectionDetails,
    ConnectionSummary,
    ServerInfo,
)
from ossdbtoolsservice.connection.contracts.connection_complete_notification import (
    ConnectionCompleteParams,
)


@dataclass
class OwnerConnectionInfo:
    """Class to hold connection information for an owner URI"""

    owner_uri: str
    connection_id: str  # As far as I can tell, this is largely unused in VSCode
    server_info: ServerInfo
    connection_summary: ConnectionSummary
    connection_details: ConnectionDetails

    @property
    def server_version(self) -> tuple[int, int, int]:
        """Get the server version as a tuple of integers"""
        split = self.server_info.server_version.split(".")
        # server_version validation is done in the ServerInfo model
        return (int(split[0]), int(split[1]), int(split[2]))

    def to_connection_complete_params(self) -> ConnectionCompleteParams:
        """Convert to ConnectionCompleteParams"""
        return ConnectionCompleteParams(
            connection_id=self.connection_id,
            owner_uri=self.owner_uri,
            server_info=self.server_info,
            connection_summary=self.connection_summary,
        )
