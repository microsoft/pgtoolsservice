# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pydantic import BaseModel

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.query.contracts import SelectionData
from ossdbtoolsservice.serialization import Serializable


class ExecutionPlanOptions(Serializable):
    include_actual_execution_plan_xml: bool
    include_estimated_execution_plan_xml: bool

    def __init__(self) -> None:
        self.include_actual_execution_plan_xml: bool = False
        self.include_estimated_execution_plan_xml: bool = False


class ExecuteRequestParamsBase(Serializable):
    owner_uri: str | None
    execution_plan_options: ExecutionPlanOptions  # TODO: Seem unused in VSCode

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Serializable] | type[BaseModel]]:
        return {"execution_plan_options": ExecutionPlanOptions}

    def __init__(self, owner_uri: str | None = None) -> None:
        self.owner_uri: str | None = owner_uri
        self.execution_plan_options: ExecutionPlanOptions = ExecutionPlanOptions()


class ExecuteStringParams(ExecuteRequestParamsBase):
    query: str | None

    def __init__(self, owner_uri: str | None = None, query: str | None = None) -> None:
        super().__init__(owner_uri=owner_uri)
        self.query: str | None = query


EXECUTE_STRING_REQUEST_METHOD = "query/executeString"
EXECUTE_STRING_REQUEST = IncomingMessageConfiguration(
    EXECUTE_STRING_REQUEST_METHOD, ExecuteStringParams
)

EXECUTE_DEPLOY_REQUEST = IncomingMessageConfiguration(
    "query/executeDeploy", ExecuteStringParams
)


class ExecuteDocumentSelectionParams(ExecuteRequestParamsBase):
    query_selection: SelectionData | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Serializable] | type[BaseModel]]:
        return {
            "query_selection": SelectionData,
            "execution_plan_options": ExecutionPlanOptions,
        }

    def __init__(self) -> None:
        super().__init__()
        self.query_selection = None


EXECUTE_DOCUMENT_SELECTION_REQUEST_METHOD = "query/executeDocumentSelection"
EXECUTE_DOCUMENT_SELECTION_REQUEST = IncomingMessageConfiguration(
    EXECUTE_DOCUMENT_SELECTION_REQUEST_METHOD, ExecuteDocumentSelectionParams
)


class ExecuteDocumentStatementParams(ExecuteRequestParamsBase):
    line: int | None
    column: int | None

    def __init__(self) -> None:
        super().__init__()
        self.line: int | None = None
        self.column: int | None = None


EXECUTE_DOCUMENT_STATEMENT_REQUEST = IncomingMessageConfiguration(
    "query/executedocumentstatement", ExecuteDocumentStatementParams
)


class ExecuteResult:
    """
    Parameters for the query execute result. Reserved for future use
    """

    def __init__(self) -> None:
        pass
