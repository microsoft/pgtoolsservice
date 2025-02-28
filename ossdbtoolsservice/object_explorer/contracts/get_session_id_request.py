from pydantic import BaseModel, ConfigDict, Field

from ossdbtoolsservice.connection.contracts.common import ConnectionDetails
from ossdbtoolsservice.hosting.message_configuration import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)


class GetSessionIdResponse(BaseModel):
    """
    Args:
        session_id (str): The ID of the session.
    """

    session_id: str = Field(alias="sessionId")

    model_config = ConfigDict(populate_by_name=True)


# For a given set of connection options, get the session ID of a previously
# created session
GET_SESSION_ID_REQUEST = IncomingMessageConfiguration(
    "objectexplorer/getsessionid", ConnectionDetails
)

OutgoingMessageRegistration.register_outgoing_message(GetSessionIdResponse)
