# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class MetadataSchemaParameters(Serializable):

    def __init__(self):
        self.owner_uri: str = None


class MetadataSchemaResponse:
    def __init__(self, metadata: str):
        self.metadata: str = metadata


METADATA_SCHEMA_REQUEST = IncomingMessageConfiguration('metadata/schema', MetadataSchemaParameters)
