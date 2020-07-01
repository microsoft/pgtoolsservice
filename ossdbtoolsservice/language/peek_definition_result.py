# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from typing import List


from ossdbtoolsservice.workspace.contracts.common import Location


class DefinitionResult:
    def __init__(self, is_error: bool, message: str, locations: List[Location]):
        self.is_error_result: bool = is_error
        self.message = message
        self.locations: [] = locations
