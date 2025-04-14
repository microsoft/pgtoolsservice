from dataclasses import dataclass
from typing import Callable


@dataclass
class EvaluatorConfig:
    name: str
    evaluator: Callable
    column_mapping: dict[str, str]
    min_passing_score: int = 4
    score_name: str | None = None
    reason_name: str | None = None