# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io

from pgsqltoolsservice.query.data_storage import FileStreamFactory, SaveAsExcelWriter, ServiceBufferFileStreamReader


class SaveAsExcelFileStreamFactory(FileStreamFactory):

    def __init__(self, params) -> None:
        FileStreamFactory.__init__(self, params)

    def create_file(self) -> str:
        raise NotImplementedError()

    def get_reader(self, file_name: str):
        return ServiceBufferFileStreamReader(io.open(file_name, 'rb'))

    def get_writer(self, file_name: str):
        return SaveAsExcelWriter(io.open(file_name, 'w'), self._params)
