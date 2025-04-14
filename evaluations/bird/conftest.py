import pytest

from evaluations.bird.evaluators.matches_gold_sql import MatchesGoldSqlEvaluator
from evaluations.evaluators.evaluator_config import EvaluatorConfig
from evaluations.runner import EvaluationRunner
from evaluations.settings import EvaluationSettings


@pytest.fixture
def runner(
    eval_settings: EvaluationSettings,
) -> EvaluationRunner:
    """Fixture to create an EvaluationRunner instance."""
    model_config = {
        "type": "azure_openai",
        "azure_endpoint": eval_settings.azure_openai_endpoint,
        "api_key": eval_settings.azure_openai_api_key,
        "azure_deployment": eval_settings.azure_openai_eval_chat_deployment_name,
    }

    return EvaluationRunner(
        eval_settings,
        EvaluatorConfig(
            name="matches_gold_sql",
            evaluator=MatchesGoldSqlEvaluator(
                model_config=model_config,
            ),
            column_mapping={
                "question": "${data.question}",
                "evidence": "${data.evidence}",
                "response": "${data.response}",
                "queries": "${data.queries}",
                "gold_sql": "${data.gold_sql}",
                "gold_sql_results": "${data.gold_sql_results}",
            },
        ),
    )
