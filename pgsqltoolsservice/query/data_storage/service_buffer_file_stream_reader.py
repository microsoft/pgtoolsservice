# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io

from pgsqltoolsservice.query.data_storage.service_buffer import ServiceBufferFileStream


class ServiceBufferFileStreamReader(ServiceBufferFileStream):

    def __init__(self, stream: io.BufferedWriter) -> None:
        ServiceBufferFileStream.__init__(self, stream)
