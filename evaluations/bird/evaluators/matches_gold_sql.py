import logging
import os

from promptflow.client import load_flow

from evaluations.logging import configure_logging

logger = logging.getLogger(__name__)


class MatchesGoldSqlEvaluator:
    def __init__(self, model_config):
        current_dir = os.path.dirname(__file__)
        prompty_path = os.path.join(current_dir, "matches_gold_sql.prompty")
        self._flow = load_flow(source=prompty_path, model={"configuration": model_config})

    def __call__(
        self,
        *,
        question: str,
        evidence: str,
        response: str,
        queries: list,  # Prompty can't handle complex types like list[str]
        gold_sql: str,
        gold_sql_results: str,
        **kwargs,
    ):
        # Ensure logging is configured;
        # this is needed for the logging in the flow to work
        # properly as it runs in a subprocess.
        configure_logging()

        logger.info(f"Running MatchesGoldSqlEvaluator for question: {question}...")

        result = self._flow(
            question=question,
            evidence=evidence or "",
            response=response,
            queries=queries,
            gold_sql=gold_sql,
            gold_sql_results=gold_sql_results,
        )
        logger.info(f"  - Got result score: {result.get('Score', 0)}")

        return {
            "matches_gold_sql": float(result.get("Score", 0)),
            "gpt_matches_gold_sql": float(result.get("Score", 0)),
            "matches_gold_sql_reason": result.get("Explanation", ""),
        }
