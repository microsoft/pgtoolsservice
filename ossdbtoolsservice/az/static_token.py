from typing import Any

from azure.core.credentials import AccessToken, TokenCredential


class StaticTokenCredential(TokenCredential):
    """
    A static token credential that always returns the same token.

    Used in PGTS as the token is passed from the client.
    """

    def __init__(self, token: str) -> None:
        self._token = token

    def get_token(self, *scopes: Any, **kwargs: Any) -> AccessToken:
        return AccessToken(token=self._token, expires_on=0)
