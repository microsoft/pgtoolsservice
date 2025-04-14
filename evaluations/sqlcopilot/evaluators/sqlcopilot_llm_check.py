import os

from promptflow.client import load_flow


class SqlCopilotLLMCheckEvaluator:
    def __init__(self, model_config):
        current_dir = os.path.dirname(__file__)
        prompty_path = os.path.join(current_dir, "sqlcopilot_llm_check.prompty")
        self._flow = load_flow(source=prompty_path, model={"configuration": model_config})

    def __call__(self, *, response: str, context: str, **kwargs):
        examples = [
            {
                "response": "ChatGPT is a conversational AI model developed by OpenAI.",
                "context": "It contains a brief explanation of ChatGPT.",
                "score": 5,
                "explanation": (
                    "The statement is correct. "
                    "The response contains a brief explanation of ChatGPT."
                ),
            }
        ]
        result = self._flow(response=response, context=context, examples=examples)
        return {
            "sqlcopilot_llm_check": float(result.get("score", 0)),
            "gpt_sqlcopilot_llm_check": float(result.get("score", 0)),
            "sqlcopilot_llm_check_reason": result.get("explanation", ""),
        }
