# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import IncomingMessageConfiguration


class TransferConnectionParams(PGTSBaseModel):
    old_owner_uri: str
    new_owner_uri: str


TRANSFER_CONNECTION_REQUEST = IncomingMessageConfiguration(
    "connection/transfer", TransferConnectionParams
)
