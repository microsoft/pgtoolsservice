# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.query_execution.contracts.common import SelectionData
from pgsqltoolsservice.serialization import Serializable


class ExecuteRequestParamsBase(Serializable):
    def __init__(self):
        self.owner_uri: str = None
        self.execution_plan_options = None      # TODO: Define/wire up ExecutionPlanOptions class


class ExecuteStringParams(ExecuteRequestParamsBase):

    def __init__(self):
        super().__init__()
        self.query: str = None


EXECUTE_STRING_REQUEST = IncomingMessageConfiguration(
    'query/executeString',
    ExecuteStringParams
)


class ExecuteDocumentSelectionParams(ExecuteRequestParamsBase):
    @classmethod
    def get_child_serializable_types(cls):
        return {'query_selection': SelectionData}

    def __init__(self):
        super().__init__()
        self.query_selection: SelectionData = None


EXECUTE_DOCUMENT_SELECTION_REQUEST = IncomingMessageConfiguration(
    'query/executeDocumentSelection',
    ExecuteDocumentSelectionParams
)


class ExecuteResult:
    """
    Parameters for the query execute result. Reserved for future use
    """

    def __init__(self):
        pass
