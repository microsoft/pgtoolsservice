import pytest

from semantic_kernel.contents import (
    AuthorRole,
    ChatHistory,
    ChatMessageContent,
    TextContent,
    FunctionCallContent,
    FunctionResultContent,
)
from ossdbtoolsservice.chat.completion.vscode_chat_completion import (
    VSCodeChatCompletionHistoryTranslator,
    VSCodeLanguageModelChatMessageRole,
    VSCodeLanguageModelTextPart,
    VSCodeLanguageModelToolCallPart,
    VSCodeLanguageModelToolResultPart,
)


@pytest.fixture
def translator():
    return VSCodeChatCompletionHistoryTranslator()


def test_translate_chat_history_with_text_content(translator):
    chat_history = ChatHistory(
        messages=[
            ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
            ChatMessageContent(
                role=AuthorRole.ASSISTANT, items=[TextContent(text="Hi there!")]
            ),
        ]
    )

    messages = translator.translate_chat_history(chat_history)

    assert len(messages) == 2
    assert messages[0].role == VSCodeLanguageModelChatMessageRole.USER
    assert isinstance(messages[0].content[0], VSCodeLanguageModelTextPart)
    assert messages[0].content[0].value == "Hello"
    assert messages[1].role == VSCodeLanguageModelChatMessageRole.ASSISTANT
    assert isinstance(messages[1].content[0], VSCodeLanguageModelTextPart)
    assert messages[1].content[0].value == "Hi there!"


def test_translate_chat_history_with_function_call(translator):
    chat_history = ChatHistory(
        messages=[
            ChatMessageContent(
                role=AuthorRole.USER, items=[TextContent(text="Call function")]
            ),
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                items=[
                    FunctionCallContent(
                        id="1", name="test_function", arguments={"arg1": "value1"}
                    )
                ],
            ),
            ChatMessageContent(
                role=AuthorRole.USER,
                items=[FunctionResultContent(id="1", result="Function result")],
            ),
        ]
    )

    messages = translator.translate_chat_history(chat_history)

    assert len(messages) == 3
    assert messages[0].role == VSCodeLanguageModelChatMessageRole.USER
    assert isinstance(messages[0].content[0], VSCodeLanguageModelTextPart)
    assert messages[0].content[0].value == "Call function"
    assert messages[1].role == VSCodeLanguageModelChatMessageRole.ASSISTANT
    assert isinstance(messages[1].content[0], VSCodeLanguageModelToolCallPart)
    assert messages[1].content[0].call_id == "1"
    assert messages[1].content[0].name == "test_function"
    assert messages[1].content[0].input == {"arg1": "value1"}
    assert messages[2].role == VSCodeLanguageModelChatMessageRole.USER
    assert isinstance(messages[2].content[0], VSCodeLanguageModelToolResultPart)
    assert messages[2].content[0].call_id == "1"
    assert isinstance(messages[2].content[0].content[0], VSCodeLanguageModelTextPart)
    assert messages[2].content[0].content[0].value == "Function result"


def test_translate_chat_history_with_function_result(translator):
    chat_history = ChatHistory(
        messages=[
            ChatMessageContent(
                role=AuthorRole.USER, items=[TextContent(text="Call function")]
            ),
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                items=[
                    TextContent(text="Let's call some functions"),
                    FunctionCallContent(
                        id="1", name="test_function", arguments={"arg1": "value1"}
                    ),
                    FunctionCallContent(
                        id="2", name="another_function", arguments={"arg2": "value2"}
                    ),
                ],
            ),
            ChatMessageContent(
                role=AuthorRole.USER,
                items=[FunctionResultContent(id="1", result="Function result")],
            ),
            ChatMessageContent(
                role=AuthorRole.USER,
                items=[FunctionResultContent(id="2", result="Second result")],
            ),
        ]
    )

    messages = translator.translate_chat_history(chat_history)

    assert len(messages) == 6
    assert messages[0].role == VSCodeLanguageModelChatMessageRole.USER
    assert isinstance(messages[0].content[0], VSCodeLanguageModelTextPart)
    assert messages[0].content[0].value == "Call function"
    assert messages[1].role == VSCodeLanguageModelChatMessageRole.ASSISTANT
    assert isinstance(messages[1].content[0], VSCodeLanguageModelTextPart)
    assert messages[1].content[0].value == "Let's call some functions"
    assert messages[2].role == VSCodeLanguageModelChatMessageRole.ASSISTANT
    assert isinstance(messages[2].content[0], VSCodeLanguageModelToolCallPart)
    assert messages[2].content[0].call_id == "1"
    assert messages[2].content[0].name == "test_function"
    assert messages[2].content[0].input == {"arg1": "value1"}
    assert messages[3].role == VSCodeLanguageModelChatMessageRole.USER
    assert isinstance(messages[3].content[0], VSCodeLanguageModelToolResultPart)
    assert messages[3].content[0].call_id == "1"
    assert isinstance(messages[3].content[0].content[0], VSCodeLanguageModelTextPart)
    assert messages[3].content[0].content[0].value == "Function result"
    assert messages[4].role == VSCodeLanguageModelChatMessageRole.ASSISTANT
    assert isinstance(messages[4].content[0], VSCodeLanguageModelToolCallPart)
    assert messages[4].content[0].call_id == "2"
    assert messages[4].content[0].name == "another_function"
    assert messages[4].content[0].input == {"arg2": "value2"}
    assert messages[5].role == VSCodeLanguageModelChatMessageRole.USER
    assert isinstance(messages[5].content[0], VSCodeLanguageModelToolResultPart)
    assert messages[5].content[0].call_id == "2"
    assert isinstance(messages[5].content[0].content[0], VSCodeLanguageModelTextPart)
    assert messages[5].content[0].content[0].value == "Second result"
