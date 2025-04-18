# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.workspace.contracts.common import Location


class DefinitionResult:
    def __init__(
        self, is_error: bool, message: str | None, locations: list[Location]
    ) -> None:
        self.is_error_result = is_error
        self.message = message
        self.locations = locations


OutgoingMessageRegistration.register_outgoing_message(DefinitionResult)
