# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ostoolsservice.hosting import IncomingMessageConfiguration
from ostoolsservice.object_explorer.contracts.expand_request import ExpandParameters

REFRESH_REQUEST = IncomingMessageConfiguration('objectexplorer/refresh', ExpandParameters)
