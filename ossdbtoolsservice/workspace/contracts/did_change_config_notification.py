# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.workspace.contracts.configuration import Configuration


class DidChangeConfigurationParams(Serializable):
    """
    Parameters received when configuration has been changed
    """

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Configuration]]:
        return {"settings": Configuration}

    def __init__(self, configuration: Configuration | None = None) -> None:
        self.settings = configuration


DID_CHANGE_CONFIG_NOTIFICATION = IncomingMessageConfiguration(
    "workspace/didChangeConfiguration", DidChangeConfigurationParams
)
