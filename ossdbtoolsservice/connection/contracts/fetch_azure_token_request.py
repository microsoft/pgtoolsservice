from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting.message_configuration import OutgoingMessageRegistration

FETCH_AZURE_TOKEN_REQUEST_METHOD = "connection/fetchAzureToken"


class FetchAzureTokenRequestParams(PGTSBaseModel):
    """Request parameters for fetching an Azure token.

    Request will return an AzureToken
    """

    account_id: str
    tenant_id: str | None


FETCH_AZURE_TOKEN_REQUEST = OutgoingMessageRegistration.register_outgoing_message(
    FetchAzureTokenRequestParams
)
