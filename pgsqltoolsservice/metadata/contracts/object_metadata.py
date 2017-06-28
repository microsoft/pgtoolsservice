# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class ObjectMetadata(object):
    """Database object metadata"""

    def __init__(self):
        self.metadata_type: int = 0
        self.metadata_type_name: str = None
        self.schema: str = None
        self.name: str = None
