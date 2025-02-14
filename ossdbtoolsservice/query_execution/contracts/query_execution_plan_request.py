from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class QueryExecutionPlanRequest(Serializable):
    owner_uri: str
    batch_index: int
    result_set_index: int

    def __init__(self):
        self.owner_uri: str = None
        self.batch_index: int = None
        self.result_set_index: int = None


class QueryExecutionResponse:
    def __init__(self):
        self.execution_plan = None


QUERY_EXECUTION_PLAN_REQUEST = IncomingMessageConfiguration(
    "query/executionPlan", QueryExecutionPlanRequest
)
