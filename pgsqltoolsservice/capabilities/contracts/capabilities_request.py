# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration


class CapabilitiesRequestParams:
    def __init__(self):
        self.host_name = None
        self.host_version = None


class CapabilitiesResult(object):
    """Defines the capabilities result contract"""

    def __init__(self, capabilities=None):
        self.capabilities = capabilities

capabilities_request = IncomingMessageConfiguration('capabilities/list', CapabilitiesRequestParams)
