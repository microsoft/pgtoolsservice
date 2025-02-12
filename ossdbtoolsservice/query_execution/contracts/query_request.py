# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.hosting import IncomingMessageConfiguration, OutgoingMessageRegistration
from ossdbtoolsservice.serialization import Serializable


class SubsetParams(Serializable):
    owner_uri: str
    batch_index: int
    result_set_index: int
    rows_start_index: int
    rows_count: int

    def __init__(self):
        self.owner_uri = None
        self.batch_index: int = None
        self.result_set_index: int = None
        self.rows_start_index: int = None
        self.rows_count: int = None


SUBSET_REQUEST = IncomingMessageConfiguration('query/subset', SubsetParams)


class QueryCancelParams(Serializable):
    owner_uri: str

    def __init__(self):
        self.owner_uri = None


CANCEL_REQUEST = IncomingMessageConfiguration('query/cancel', QueryCancelParams)


class QueryDisposeParams(Serializable):
    owner_uri: str

    def __init__(self):
        self.owner_uri = None


DISPOSE_REQUEST = IncomingMessageConfiguration('query/dispose', QueryDisposeParams)


class QueryCancelResult:
    """Parameters to return as the result of a query dispose request"""
    messages: str

    def __init__(self, messages: str = None):
        # Optional error messages during query cancellation that can be sent back
        # Set to none if no errors
        self.messages = messages


OutgoingMessageRegistration.register_outgoing_message(QueryCancelResult)
