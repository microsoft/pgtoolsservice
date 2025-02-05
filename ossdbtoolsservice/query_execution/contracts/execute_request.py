# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.query.contracts import SelectionData
from ossdbtoolsservice.serialization import Serializable


class ExecutionPlanOptions(Serializable):
    include_actual_execution_plan_xml: bool
    include_estimated_execution_plan_xml: bool

    def __init__(self):
        self.include_actual_execution_plan_xml: bool = False
        self.include_estimated_execution_plan_xml: bool = False


class ExecuteRequestParamsBase(Serializable):
    owner_uri: str
    execution_plan_options: ExecutionPlanOptions

    @classmethod
    def get_child_serializable_types(cls):
        return {'execution_plan_options': ExecutionPlanOptions}

    def __init__(self):
        self.owner_uri: str = None
        self.execution_plan_options: ExecutionPlanOptions = ExecutionPlanOptions()


class ExecuteStringParams(ExecuteRequestParamsBase):
    query: str

    def __init__(self):
        super().__init__()
        self.query: str = None


EXECUTE_STRING_REQUEST = IncomingMessageConfiguration(
    'query/executeString',
    ExecuteStringParams
)

EXECUTE_DEPLOY_REQUEST = IncomingMessageConfiguration(
    'query/executeDeploy',
    ExecuteStringParams
)


class ExecuteDocumentSelectionParams(ExecuteRequestParamsBase):
    query_selection: SelectionData

    @classmethod
    def get_child_serializable_types(cls):
        return {'query_selection': SelectionData, 'execution_plan_options': ExecutionPlanOptions}

    def __init__(self):
        super().__init__()
        self.query_selection: SelectionData = None


EXECUTE_DOCUMENT_SELECTION_REQUEST = IncomingMessageConfiguration(
    'query/executeDocumentSelection',
    ExecuteDocumentSelectionParams
)


class ExecuteDocumentStatementParams(ExecuteRequestParamsBase):
    line: int
    column: int

    def __init__(self):
        super().__init__()
        self.line: int = None
        self.column: int = None


EXECUTE_DOCUMENT_STATEMENT_REQUEST = IncomingMessageConfiguration(
    'query/executedocumentstatement',
    ExecuteDocumentStatementParams
)


class ExecuteResult:
    """
    Parameters for the query execute result. Reserved for future use
    """

    def __init__(self):
        pass
