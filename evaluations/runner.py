import datetime
import json
from tempfile import TemporaryDirectory
from typing import Any, Callable

from azure.ai.evaluation import (
    AzureAIProject,
    evaluate,
)

from evaluations.eval_inputs import EvalInputs
from evaluations.evaluators.evaluator_config import EvaluatorConfig
from evaluations.settings import EvaluationSettings


class EvaluationRunner:
    def __init__(self, eval_settings: EvaluationSettings, *evaluators: EvaluatorConfig):
        self.eval_settings = eval_settings
        self.configs = evaluators

    def get_evaluators(self) -> dict[str, Callable]:
        return {config.name: config.evaluator for config in self.configs}

    def get_evaluator_configs(self) -> dict[str, Any]:
        return {
            config.name: {"column_mapping": config.column_mapping} for config in self.configs
        }

    def run_evaluations(
        self,
        suite_name: str,
        inputs: EvalInputs,
    ) -> dict[str, Any]:
        aif_project = AzureAIProject(
            subscription_id=self.eval_settings.azureai_subscription_id,
            resource_group_name=self.eval_settings.azureai_resource_group,
            project_name=self.eval_settings.azureai_project_name,
        )

        with TemporaryDirectory() as temp_dir:
            data_file = f"{temp_dir}/data.jsonl"            
            #data_file = "/home/rob/proj/vscode/pgtoolsservice/data.json"
            inputs.save_data(data_file)

            # Evaluate the response
            time_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            result = evaluate(
                evaluation_name=(
                    "PostgreSQL VSCode GitHub Copilot Evaluation: "
                    f"{suite_name} ({time_string})"
                ),
                data=data_file,
                evaluators=self.get_evaluators(),
                evaluator_configs=self.get_evaluator_configs(),
                azure_ai_project=aif_project,
            )

        fails: dict[str, dict[str, tuple[int, str]]] = {}
        for row in result["rows"]:
            test_id = inputs.get_id_from_result(row)
            min_score = inputs.get_min_score_from_result(row)
            for config in self.configs:
                score_name = (
                    f"outputs.{config.name}.{config.score_name}"
                    if config.score_name
                    else f"outputs.{config.name}.{config.name}"
                )
                reason_name = (
                    f"outputs.{config.name}.{config.reason_name}"
                    if config.reason_name
                    else f"outputs.{config.name}.{config.name}_reason"
                )
                score = int(row[score_name])
                reason = row[reason_name]
                if score < min_score:
                    fails.setdefault(test_id, {})[config.name] = (score, reason)

        return fails