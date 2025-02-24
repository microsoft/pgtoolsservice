from pydantic import BaseModel

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

    session_id: str


# For a given set of connection options, get the session ID of a previously
# created session
GET_SESSION_ID_REQUEST = IncomingMessageConfiguration(
    "objectexplorer/getsessionid", ConnectionDetails
)

OutgoingMessageRegistration.register_outgoing_message(GetSessionIdResponse)
