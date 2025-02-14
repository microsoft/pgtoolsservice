# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.capabilities.contracts import FeatureMetadataProvider
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.query.contracts import SaveResultsRequestParams


class SaveResultRequestResult:
    messages: str

    def __init__(self):
        self.messages: str = None


class SaveResultsAsCsvRequestParams(SaveResultsRequestParams):
    include_headers: bool
    delimiter: str

    def __init__(self):
        super().__init__()
        self.include_headers: bool = None
        self.delimiter: str = ","


class SaveResultsAsJsonRequestParams(SaveResultsRequestParams):
    def __init__(self):
        super().__init__()


class SaveResultsAsExcelRequestParams(SaveResultsRequestParams):
    include_headers: bool

    def __init__(self):
        super().__init__()
        self.include_headers: bool = None


SAVE_AS_CSV_REQUEST = IncomingMessageConfiguration(
    "query/saveCsv", SaveResultsAsCsvRequestParams
)

SAVE_AS_JSON_REQUEST = IncomingMessageConfiguration(
    "query/saveJson", SaveResultsAsJsonRequestParams
)

SAVE_AS_EXCEL_REQUEST = IncomingMessageConfiguration(
    "query/saveExcel", SaveResultsAsExcelRequestParams
)

SERIALIZATION_OPTIONS = FeatureMetadataProvider(True, "serializationService", [])

OutgoingMessageRegistration.register_outgoing_message(SaveResultRequestResult)
