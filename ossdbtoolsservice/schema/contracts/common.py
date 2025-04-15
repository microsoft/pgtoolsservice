# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.core.models import PGTSBaseModel


class SessionIdContainer(PGTSBaseModel):
    session_id: str

__all__ = [
    "SessionIdContainer"
]