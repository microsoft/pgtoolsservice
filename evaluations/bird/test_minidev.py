import json
import logging
from pathlib import Path
from typing import Any

from evaluations.completion_client import CompletionClient
from evaluations.eval_inputs import EvalInputs
from evaluations.runner import EvaluationRunner
from tests_v2.test_utils.message_server_client_wrapper import MockMessageServerClientWrapper

HERE = Path(__file__).parent
MINIDEV_DATA = HERE / "bird_mini_dev_pg.json"

logger = logging.getLogger(__name__)


def run_bird_evaluation(
    suite_name: str,
    db_id: str,
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
    run_only_tests: list[int] | None = None,
) -> None:
    """Run the BIRD evaluation."""    
    dbname = "postgres"

    # Implementation of the evaluation logic goes here
    with open(MINIDEV_DATA) as f:
        minidev_data = json.load(f)

    by_db = {}
    for item in minidev_data:
        by_db.setdefault(item["db_id"], []).append(item)

    tests = by_db.get(db_id)
    if tests is None:
        raise ValueError(f"Unknown db_id: {db_id}")

    if run_only_tests:
        suite_name += f" (filtered: {len(run_only_tests)} tests)"
        tests = [test for test in tests if test["question_id"] in run_only_tests]

    logger.info(f"  --- BIRD: Running {suite_name} ---")
    logger.info(f"Preparing to run {len(tests)} tests")

    with completion_client.connect(
        suite_name,
        dbname,
    ):
        logger.info(f"Connected to {dbname}")
        data: list[dict[str, Any]] = []
        for test in tests:
            question_id = test["question_id"]
            question = test["question"]
            evidence = test["evidence"]
            gold_sql = test["SQL"]
            difficulty = test["difficulty"]

            logger.info(f"Getting gold sql for question {question_id}...")

            # Get result of gold sql query
            subset, summary = mock_server_client_wrapper.execute_query(
                suite_name, gold_sql, timeout=10
            )            

            row_count = subset.result_subset.row_count if subset else 0
            logger.info(f"   - Got {row_count} rows")

            # Add headers
            gold_sql_results: str = (
                '"'
                + '","'.join([col.column_name or "" for col in summary.column_info])
                + '"\n'
            )

            for row in subset.result_subset.rows if subset else []:
                gold_sql_results += (
                    '"'
                    + '","'.join(
                        [cell.display_value if not cell.is_null else "NULL" for cell in row]
                    )
                    + '"\n'
                )

            logger.info(f"Getting response for question {question_id}...")

            prompt = f"{question} {evidence}"
            result = completion_client.get_response(prompt)

            logger.info(f"   - Got response: {result.response}")

            test_entry = {
                "question_id": question_id,
                "question": question,
                "evidence": evidence,
                "gold_sql": gold_sql,
                "gold_sql_results": gold_sql_results,
                "difficulty": difficulty,
                "response": result.response,
                "queries": result.queries_executed,
            }

            data.append(test_entry)

    logger.info("Running evaluation...")
    fails = runner.run_evaluations(
        suite_name,
        inputs=EvalInputs(
            data=data,
            test_id_field="question_id",
            min_score_field=None,
            min_score_default=4,
        ),
    )

    if fails:        
        logger.info("The following questions failed:")
    for query, reasons in fails.items():
        logger.info(f"Query: {query}")
        for evaluator, (score, reason) in reasons.items():
            logger.info(f"  {evaluator} score: {score}")
            logger.info(f"  {evaluator} reason: {reason}")
    assert not fails


def test_bird_minidev_debit_card_specializing(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev debit card specializing evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: debit card specializing",
        db_id="debit_card_specializing",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
    )


# formula_1 db
def test_bird_minidev_formula_1(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev formula 1 evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: formula 1",
        db_id="formula_1",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
    )


# codebase_community
def test_bird_minidev_codebase_community(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev codebase community evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: codebase community",
        db_id="codebase_community",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
        # run_only_tests=[563]
    )

# california_schools
def test_bird_minidev_california_schools(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev california schools evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: california schools",
        db_id="california_schools",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
    )

# card_games
def test_bird_minidev_card_games(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev card games evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: card games",
        db_id="card_games",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
        # run_only_tests=[371],
    )

# european_football_2
def test_bird_minidev_european_football_2(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev european football 2 evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: european football 2",
        db_id="european_football_2",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
    )

# financial
def test_bird_minidev_financial(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev financial evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: financial",
        db_id="financial",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
    )

# student_club
def test_bird_minidev_student_club(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev student club evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: student club",
        db_id="student_club",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
    )

# superhero
def test_bird_minidev_superhero(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev superhero evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: superhero",
        db_id="superhero",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
    )

# thrombosis_prediction
def test_bird_minidev_thrombosis_prediction(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev thrombosis prediction evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: thrombosis prediction",
        db_id="thrombosis_prediction",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
    )

# toxicology
def test_bird_minidev_toxicology(
    completion_client: CompletionClient,
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    runner: EvaluationRunner,
) -> None:
    """Test the bird minidev toxicology evaluation."""
    run_bird_evaluation(
        suite_name="BIRD (minidev) db: toxicology",
        db_id="toxicology",
        completion_client=completion_client,
        mock_server_client_wrapper=mock_server_client_wrapper,
        runner=runner,
    )