class AzureTokenRefreshError(Exception):
    """Exception raised when Azure token refresh fails."""

    pass


class GetConnectionTimeout(Exception):
    """Exception raised when getting a connection times out."""

    def __init__(
        self, pool_size: int, pool_max: int, active_tx: int, connection_error_message: str
    ) -> None:
        self.pool_size = pool_size
        self.pool_max = pool_max
        self.active_tx = active_tx
        self.connection_error_message = connection_error_message
        super().__init__(
            "Timeout getting connection from pool. "
            f"pool size: {pool_size}, max: {pool_max}, active tx: {active_tx}"
            + connection_error_message
        )


class ConnectionError(Exception):
    """Exception raised when there is a connection error."""

    pass
