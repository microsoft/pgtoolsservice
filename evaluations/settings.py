from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class EvaluationSettings(BaseSettings):
    azure_openai_api_version: str = "2023-05-15"
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_chat_deployment_name: str
    azure_openai_eval_chat_deployment_name: str

    azureai_subscription_id: str
    azureai_resource_group: str
    azureai_project_name: str

    connection_string: str

    model_config = SettingsConfigDict(env_prefix="PGTS_EVAL_")

    eval_log_file: Path | str = (Path(__file__).parent / "evaluation.log").absolute()
    pgts_log_dir: Path | str = Path(__file__).parent.absolute()

@lru_cache(maxsize=1)
def get_settings() -> EvaluationSettings:
    """Get the evaluation settings."""
    return EvaluationSettings(_env_file=".env")  # pyright: ignore