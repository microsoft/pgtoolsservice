# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading                    # noqa
from typing import List, Optional, Dict   # noqa

from pgsmo import Server            # noqa
from pgsqltoolsservice.connection.contracts import ConnectionDetails


class ObjectExplorerSession:
    def __init__(self, session_id: str, params: ConnectionDetails):
        self.connection_details: ConnectionDetails = params
        self.id: str = session_id
        self.is_ready: bool = False
        self.server: Optional[Server] = None

        self.init_task: Optional[threading.Thread] = None
        self.expand_tasks: Dict[str, threading.Thread] = {}
        self.refresh_tasks: Dict[str, threading.Thread] = {}
