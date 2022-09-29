# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.query.contracts import SaveResultsRequestParams
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.capabilities.contracts import FeatureMetadataProvider


class SaveResultRequestResult:

    def __init__(self):
        self.messages: str = None


class SaveResultsAsCsvRequestParams(SaveResultsRequestParams):

    def __init__(self):
        super().__init__()
        self.include_headers: bool = None


class SaveResultsAsJsonRequestParams(SaveResultsRequestParams):

    def __init__(self):
        super().__init__()


class SaveResultsAsExcelRequestParams(SaveResultsRequestParams):

    def __init__(self):
        super().__init__()
        self.include_headers: bool = None

class SaveResultsAsXmlRequestParams(SaveResultsRequestParams):

    def __init__(self):
        super().__init__()
        self.include_headers: bool = None


SAVE_AS_CSV_REQUEST = IncomingMessageConfiguration(
    'query/saveCsv',
    SaveResultsAsCsvRequestParams
)

SAVE_AS_JSON_REQUEST = IncomingMessageConfiguration(
    'query/saveJson',
    SaveResultsAsJsonRequestParams
)

SAVE_AS_EXCEL_REQUEST = IncomingMessageConfiguration(
    'query/saveExcel',
    SaveResultsAsExcelRequestParams
)

SAVE_AS_XML_REQUEST = IncomingMessageConfiguration(
    'query/saveXml',
    SaveResultsAsXmlRequestParams
)

SERIALIZATION_OPTIONS = FeatureMetadataProvider(
    True,
    'serializationService',
    []
)
