import time

from ossdbtoolsservice.core.models import PGTSBaseModel


class AzureToken(PGTSBaseModel):
    token: str
    expiry: int
    """Token and expiry time for Azure authentication.
    
    In Unix time format, the number of seconds elapsed since midnight,
    January 1, 1970 Universal Coordinated Time (UTC).
    """

    def is_azure_token_expired(self) -> bool:
        """Returns True if the token is expired or expiring within 30 seconds."""
        now = int(time.time())
        max_tolerance = 30

        return self.expiry <= (now + max_tolerance)
