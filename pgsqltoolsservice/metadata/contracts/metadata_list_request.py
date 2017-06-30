# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.connection.contracts.common import ConnectionDetails, ConnectionType  # noqa
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata
import pgsqltoolsservice.utils as utils

class MetadataListParameters:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.owner_uri: str = None

class MetadataListResponse:
    def __init__(self):
        self.Metadata: List[ObjectMetadata] = None

METADATA_LIST_REQUEST = IncomingMessageConfiguration('metadata/list', MetadataListParameters)