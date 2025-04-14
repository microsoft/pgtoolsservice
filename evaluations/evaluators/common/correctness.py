import os

from azure.ai.evaluation._common.utils import (
    # Importing a private function for now
    parse_quality_evaluator_reason_score,  # type: ignore
)
from promptflow.client import load_flow


class CorrectnessEvaluator:
    def __init__(self, model_config):
        current_dir = os.path.dirname(__file__)
        prompty_path = os.path.join(current_dir, "correctness.prompty")
        self._flow = load_flow(source=prompty_path, model={"configuration": model_config})

    def __call__(self, *, query: str, context: str, response: str, **kwargs):
        try:
            llm_response = self._flow(query=query, context=context, response=response)
        except Exception as e:
            print(f"Error in flow execution: {e}")
            raise
        try:
            score, reason = parse_quality_evaluator_reason_score(llm_response)
            return {
                "correctness": float(score),
                "gpt_correcteness": float(score),
                "correctness_reason": reason,
            }
        except Exception:
            response = llm_response
        return response
