import json
from tempfile import TemporaryDirectory
from typing import Any

import pytest
from azure.ai.evaluation import (
    AzureAIProject,
    AzureOpenAIModelConfiguration,
    RelevanceEvaluator,
    evaluate,
)

from evaluations.chat_service_wrapper import ChatServiceWrapper
from evaluations.evaluators.correctness import CorrectnessEvaluator
from evaluations.settings import EvaluationSettings
from ossdbtoolsservice.chat.messages import ChatCompletionRequestParams


@pytest.mark.parametrize(
    "inputs",
    [
        [
            {
                "query": "Create a table named account, linked to the customer table, "
                "that has a column named email address.",
                "context": "The copilot should ask to confirm a sql to modify the database "
                "by asking the user to refer to it by name. The customer table has a "
                "primary key of customer_id. The response should present a SQL statement "
                "to the user.",
            }
        ],
        [
            {
                "query": "What is the table with the most rows in my database?",
                "context": "The payment table has the most rows.",
            },
            {
                "query": "What tables are in my database?",
                "context": (
                    "Database contains user tables: "
                    "actor,address,category,city,country,customer,"
                    "film,film_actor,film_category,inventory,language,"
                    "payment,rental,staff,store"
                ),
            },
        ],
    ],
)
def test_evals(
    chat_service_wrapper: ChatServiceWrapper,
    eval_settings: EvaluationSettings,
    inputs: list[dict[str, str]],
) -> None:
    """Test the first evaluation."""

    model_config = AzureOpenAIModelConfiguration(
        api_key=eval_settings.azure_openai_api_key,
        azure_deployment=eval_settings.azure_openai_eval_chat_deployment_name,
        azure_endpoint=eval_settings.azure_openai_endpoint,
    )

    relevance_eval = RelevanceEvaluator(
        model_config=model_config,
    )
    correctness_eval = CorrectnessEvaluator(
        model_config=model_config,
    )

    data: list[dict[str, Any]] = []
    for input in inputs:
        prompt = input["query"]
        context = input["context"]

        completion_request = ChatCompletionRequestParams(
            prompt=prompt,
            history=[],
            owner_uri="test",
            profile_name="testdb",
        )

        response = chat_service_wrapper.get_response(completion_request)
        data.append(
            {
                "query": prompt,
                "response": response.response,
                "context": context,
                "queriesExecuted": response.queries_executed,
            }
        )

    aif_project = AzureAIProject(
        subscription_id=eval_settings.azureai_subscription_id,
        resource_group_name=eval_settings.azureai_resource_group,
        project_name=eval_settings.azureai_project_name,
    )

    with TemporaryDirectory() as temp_dir:
        data_file = f"{temp_dir}/data.jsonl"
        data_file = "data.jsonl"
        with open(data_file, "w") as temp_file:
            for d in data:
                temp_file.write(f"{json.dumps(d)}\n")

        # Evaluate the response
        result = evaluate(
            evaluation_name="PostgreSQL GitHub Copilot Chatbot - Evaluation",
            data=data_file,
            evaluators={
                "relevance": relevance_eval,
                "correctness": correctness_eval,
            },
            # column mapping
            evaluator_config={
                "relevance": {
                    "column_mapping": {
                        "query": "${data.query}",
                        "response": "${data.response}",
                    }
                },
                "correctness": {
                    "column_mapping": {
                        "query": "${data.query}",
                        "context": "${data.context}",
                        "response": "${data.response}",
                    }
                },
            },
            azure_ai_project=aif_project,
        )

    fails: dict[str, dict[str, tuple[int, str]]] = {}
    for row in result["rows"]:
        query = row["inputs.query"]
        relevance = row["outputs.relevance.relevance"]
        relevance_reason = row["outputs.relevance.relevance_reason"]
        correctness = row["outputs.correctness.correctness"]
        correctness_reason = row["outputs.correctness.correctness_reason"]
        if correctness < 4:
            fails.setdefault(query, {})["correctness"] = (correctness, correctness_reason)
        if relevance < 4:
            fails.setdefault(query, {})["relevance"] = (relevance, relevance_reason)

    if fails:
        print("The following queries failed:")
    for query, reasons in fails.items():
        print(f"Query: {query}")
        for evaluator, (score, reason) in reasons.items():
            print(f"  {evaluator} score: {score}")
            print(f"  {evaluator} reason: {reason}")
    assert not fails
