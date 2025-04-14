import json
from typing import Any


class EvalInputs:
    def __init__(
        self,
        data: list[dict[str, Any]],
        test_id_field: str,
        min_score_field: str | None,
        min_score_default: int,
    ) -> None:
        self.data = data
        self.test_id_field = test_id_field
        self.min_score_field = min_score_field
        self.min_score_default = min_score_default

    def save_data(self, file_path: str) -> None:
        """Save the data to a JSON file."""
        with open(file_path, "w") as f:
            for d in self.data:
                f.write(f"{json.dumps(d)}\n")

    def get_id_from_result(self, result: dict[str, Any]) -> str:
        """Get the test ID from the result."""
        return result[f"inputs.{self.test_id_field}"]

    def get_min_score_from_result(self, result: dict[str, Any]) -> int:
        """Get the min score from the result."""
        return int(
            result.get(f"inputs.{self.min_score_field}", self.min_score_default)
            if self.min_score_field
            else self.min_score_default
        )
