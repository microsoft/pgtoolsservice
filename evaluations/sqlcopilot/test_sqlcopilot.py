from pathlib import Path
from typing import Any

from evaluations.completion_client import CompletionClient
from evaluations.eval_inputs import EvalInputs
from evaluations.evaluators.evaluator_config import EvaluatorConfig
from evaluations.runner import EvaluationRunner
from evaluations.settings import EvaluationSettings
from evaluations.sqlcopilot.evaluators.sqlcopilot_llm_check import SqlCopilotLLMCheckEvaluator
from evaluations.sqlcopilot.utils import parse_yaml_to_test_map


def run_sqlcopilot_evaluation(
    suite_name: str,
    eval_file: str,
    db_name: str,
    completion_client: CompletionClient,
    eval_settings: EvaluationSettings,
    run_only_tests: list[str] | None = None,
) -> None:
    if run_only_tests:
        suite_name += f" (filtered: {len(run_only_tests)} tests)"

    with completion_client.connect(db_name, suite_name):
        model_config = {
            "type": "azure_openai",
            "azure_endpoint": eval_settings.azure_openai_endpoint,
            "api_key": eval_settings.azure_openai_api_key,
            "azure_deployment": eval_settings.azure_openai_eval_chat_deployment_name,
        }

        runner = EvaluationRunner(
            eval_settings,
            EvaluatorConfig(
                name="sqlcopilot_llm_check",
                evaluator=SqlCopilotLLMCheckEvaluator(model_config=model_config),
                column_mapping={
                    "context": "${data.context}",
                    "response": "${data.response}",
                },
            ),
        )

        test_map = parse_yaml_to_test_map(file_path=Path(__file__).parent / eval_file)

        data: list[dict[str, Any]] = []
        for name, test_case in test_map.items():
            if run_only_tests and name not in run_only_tests:
                continue
            prompt = test_case["prompt"]
            context = test_case["context"]
            min_score = test_case.get("minScore", 4)

            # Replace system instructions in prompt.
            prompt = prompt.replace(
                "You must run the final query and summarize the query results "
                "in detail to answer the user "
                "question. and don't show your work.",
                "",
            ).strip()

            prompt = prompt.replace(
                "You must not run the final query, you should only return the generated "
                "tsql script to answer the user question.",
                "Just give me the query.",
            ).strip()

            response = completion_client.get_response(prompt)

            data.append(
                {
                    "suite": suite_name,
                    "name": name,
                    "query": prompt,
                    "response": response.response,
                    "context": context,
                    "queriesExecuted": response.queries_executed,
                    "minScore": min_score,
                }
            )

        inputs = EvalInputs(
            data=data,
            test_id_field="name",
            min_score_field="minScore",
            min_score_default=3,
        )

        fails = runner.run_evaluations(suite_name=suite_name, inputs=inputs)

        if fails:
            print("The following queries failed:")
        for query, reasons in fails.items():
            print(f"Query: {query}")
            for evaluator, (score, reason) in reasons.items():
                print(f"  {evaluator} score: {score}")
                print(f"  {evaluator} reason: {reason}")
        assert not fails


def test_AdventureWorks2012(
    completion_client: CompletionClient,
    eval_settings: EvaluationSettings,
) -> None:
    run_sqlcopilot_evaluation(
        suite_name="AdventureWorks2012",
        eval_file="AdventureWorks2012.yaml",
        db_name="adventureworks",
        completion_client=completion_client,
        eval_settings=eval_settings,
        # run_only_tests=["Q3"],
    )


def test_AdventureWorksDWInventory(
    completion_client: CompletionClient,
    eval_settings: EvaluationSettings,
) -> None:
    run_sqlcopilot_evaluation(
        suite_name="AdventureWorksDWInventory",
        eval_file="AdventureWorksDWInventory.yaml",
        db_name="adventureworksdw2014",
        completion_client=completion_client,
        eval_settings=eval_settings,
        # run_only_tests=[f"Q{i}" for i in range(1,11)],
        # run_only_tests=["Q6"],
    )


def test_AdventureWorksDWSales(
    completion_client: CompletionClient,
    eval_settings: EvaluationSettings,
) -> None:
    run_sqlcopilot_evaluation(
        suite_name="AdventureWorksDWSales",
        eval_file="AdventureWorksDWSales.yaml",
        db_name="adventureworksdw2014",
        completion_client=completion_client,
        eval_settings=eval_settings,
    )


def test_AdventureWorksLT(
    completion_client: CompletionClient,
    eval_settings: EvaluationSettings,
) -> None:
    run_sqlcopilot_evaluation(
        suite_name="AdventureWorksLT",
        eval_file="AdventureWorksLT.yaml",
        db_name="adventureworkslt2022",
        completion_client=completion_client,
        eval_settings=eval_settings,
    )


def test_AdventureWorksLTNonSelect(
    completion_client: CompletionClient,
    eval_settings: EvaluationSettings,
) -> None:
    run_sqlcopilot_evaluation(
        suite_name="AdventureWorksLTNonSelect",
        eval_file="AdventureWorksLTNonSelect.yaml",
        db_name="adventureworkslt2022",
        completion_client=completion_client,
        eval_settings=eval_settings,
    )


def test_SU_Design_AWLT(
    completion_client: CompletionClient,
    eval_settings: EvaluationSettings,
) -> None:
    run_sqlcopilot_evaluation(
        suite_name="SU_Design_AWLT",
        eval_file="SU_Design_AWLT.yaml",
        db_name="adventureworkslt2022",
        completion_client=completion_client,
        eval_settings=eval_settings,
    )
