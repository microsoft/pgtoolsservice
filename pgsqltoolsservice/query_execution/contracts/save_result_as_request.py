# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.query.contracts import SaveResultsRequestParams
from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.capabilities.contracts import FeatureMetadataProvider


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

SERIALIZATION_OPTIONS = FeatureMetadataProvider(
    True,
    'serializationService',
    []
)
