from pgsqltoolsservice.workspace.contracts.common import Location  # noqa


class DefinitionResult:
    def __init__(self, is_error: bool, msg: str, locations: []):
        self.is_error_result: bool = is_error
        self.message = msg
        self.locations: [] = locations
