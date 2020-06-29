# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.object_explorer.contracts.expand_request import ExpandParameters

REFRESH_REQUEST = IncomingMessageConfiguration('objectexplorer/refresh', ExpandParameters)
