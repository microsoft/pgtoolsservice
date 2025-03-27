from ossdbtoolsservice.chat.prompts import system_message_prompt
from ossdbtoolsservice.query_execution.contracts.message_notification import ResultMessage


def test_system_prompt_no_data() -> None:
    prompt = system_message_prompt(
        doc_text="",
        selected_doc_text="",
        db_context="",
        profile_name="",
        is_azure_pg=False,
        result_messages=None,
    )

    assert prompt


def test_system_prompt_with_data() -> None:
    prompt = system_message_prompt(
        doc_text="Sample doc text",
        selected_doc_text="Sample selected doc text",
        db_context="Sample db context",
        profile_name="Sample profile name",
        is_azure_pg=True,
        result_messages=[
            ResultMessage(
                batch_id=1,
                is_error=False,
                time="2023-10-01T12:00:00Z",
                message="Sample result message 1",
            ),
            ResultMessage(
                batch_id=1,
                is_error=True,
                time="2023-10-01T12:00:01Z",
                message="Sample error message 1",
            ),
        ],
    )

    assert prompt
