# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class DMPServerCapabilities(object):
    """Defines the DMP server capabilities"""

    def __init__(
            self,
            protocolVersion=None,
            providerName=None,
            providerDisplayName=None,
            connectionProvider=None):
        self.protocolVersion = protocolVersion
        self.providerName = providerName
        self.providerDisplayName = providerDisplayName
        self.connectionProvider = connectionProvider
