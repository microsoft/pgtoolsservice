# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.metadata.contracts.object_metadata import ObjectMetadata  # noqa
from typing import List  # noqa
from ossdbtoolsservice.serialization import Serializable


class MetadataListParameters(Serializable):

    def __init__(self):
        self.owner_uri: str = None


class MetadataListResponse:
    def __init__(self, metadata: List[ObjectMetadata]):
        self.metadata: List[ObjectMetadata] = metadata


METADATA_LIST_REQUEST = IncomingMessageConfiguration('metadata/list', MetadataListParameters)
