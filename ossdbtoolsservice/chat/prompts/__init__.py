import json
from pathlib import Path
from typing import Any

from jinja2 import StrictUndefined, Template

from ossdbtoolsservice.chat.constants import (
    FETCH_DB_OBJECTS_FUNCTION_NAME,
    FETCH_FULL_SCHEMA_FUNCTION_NAME,
)
from ossdbtoolsservice.query_execution.contracts.message_notification import ResultMessage

HERE = Path(__file__).parent


def template(template_text: str, **values: Any) -> str:
    template = Template(template_text, undefined=StrictUndefined)
    return template.render(**values)


def load_prompt(prompt_name: str, **values: Any) -> str:
    prompt = prompt_name + ".md"
    template_txt = (HERE / prompt).read_text()
    return template(template_txt, **values).strip()


def system_message_prompt(
    doc_text: str | None,
    selected_doc_text: str | None,
    db_context: str | None,
    profile_name: str | None,
    is_azure_pg: bool,
    result_messages: list[ResultMessage] | None = None,
) -> str:
    return load_prompt(
        "system_message_v2",
        doc_text=doc_text,
        selected_doc_text=selected_doc_text,
        db_context=db_context,
        profile_name=profile_name,
        is_azure_pg=is_azure_pg,
        result_messages=result_messages,
        fetch_db_objects_name=FETCH_DB_OBJECTS_FUNCTION_NAME,
        fetch_full_schema_name=FETCH_FULL_SCHEMA_FUNCTION_NAME,
    )


def tool_call_to_system_message_prompt(
    call_id: str, function_name: str, function_input: dict[str, Any], result: str
) -> str:
    return load_prompt(
        "tool_call_to_system_message_prompt",
        call_id=call_id,
        function_name=function_name,
        function_input_str=json.dumps(function_input),
        result=result,
    )
