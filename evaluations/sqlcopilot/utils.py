from pathlib import Path

import yaml

DEFAULT_MIN_SCORE = 3


def parse_yaml_to_test_map(file_path: str | Path) -> dict[str, dict[str, str]]:
    """
    Reads a YAML file and produces a map of test name -> { "prompt", "context" }.
    """
    with open(file_path) as file:
        data = yaml.safe_load(file)

    test_map = {}
    for test_case in data.get("TestCases", []):
        test_name = test_case.get("Name")
        for command in test_case.get("Commands", []):
            prompt = command.get("Prompt")
            for evaluation in command.get("RequiredEvaluations", []):
                if evaluation.get("Criteria") == "LLMCheck":
                    context = evaluation.get("Parameters", {}).get("Definition")
                    minScore = evaluation.get("MinScore", DEFAULT_MIN_SCORE)
                    if test_name and prompt and context:
                        test_map[test_name] = {
                            "prompt": prompt,
                            "context": context,
                            "minScore": minScore,
                        }
    return test_map
