from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class QueryExecutionPlanRequest(Serializable):
    owner_uri: str | None
    batch_index: int | None
    result_set_index: int | None

    def __init__(self) -> None:
        self.owner_uri = None
        self.batch_index = None
        self.result_set_index = None


class QueryExecutionResponse:
    def __init__(self) -> None:
        self.execution_plan = None


QUERY_EXECUTION_PLAN_REQUEST = IncomingMessageConfiguration(
    "query/executionPlan", QueryExecutionPlanRequest
)
