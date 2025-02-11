from pathlib import Path
from typing import Any
from jinja2 import StrictUndefined, Template

HERE = Path(__file__).parent


def template(template_text: str, **values: Any) -> str:
    template = Template(template_text, undefined=StrictUndefined)
    return template.render(**values)


def load_prompt(prompt_name: str, **values):
    prompt = prompt_name + ".md"
    template_txt = (HERE / prompt).read_text()
    return template(template_txt, **values).strip()


def system_message_prompt(doc_text: str | None, db_context: str | None) -> str:
    return load_prompt("system_message", doc_text=doc_text, db_context=db_context)
