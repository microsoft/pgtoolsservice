# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import xml.etree.ElementTree as ET
import xml.dom.minidom
from typing import List

from ossdbtoolsservice.query.data_storage.save_as_writer import SaveAsWriter
from ossdbtoolsservice.query.contracts import DbColumn, DbCellValue, SaveResultsRequestParams


class SaveAsXmlWriter(SaveAsWriter):

    def __init__(self, stream: io.BufferedWriter, params: SaveResultsRequestParams) -> None:
        SaveAsWriter.__init__(self, stream, params)
        self._RootElementTag = "data"
        self._ItemElementTag = "row"

        self._data = ET.Element(self._RootElementTag)

    def write_row(self, row: List[DbCellValue], columns: List[DbColumn]):
    
        elementRow = ET.SubElement(self._data, self._ItemElementTag)

        column_start_index = self.get_start_index()
        column_end_index = self.get_end_index(columns)

        for index in range(column_start_index, column_end_index):
            column_name = columns[index].column_name
            column_value = row[index].display_value
            elementColumn = ET.SubElement(elementRow, column_name)
            elementColumn.text = column_value

    def complete_write(self):
        xmlAsString = ET.tostring(self._data, "utf-8")
        prettyXml = xml.dom.minidom.parseString(xmlAsString).toprettyxml()
        self._file_stream.write(prettyXml)
