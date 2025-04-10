from dataclasses import dataclass

from semantic_kernel.contents import (
    ChatHistory,
    FunctionCallContent,
    FunctionResultContent,
)
from semantic_kernel.contents import (
    ChatMessageContent as SKChatMessageContent,
)

from ossdbtoolsservice.chat.messages import ChatMessageContent


@dataclass
class ToolCallRecord:
    call: FunctionCallContent
    result: FunctionResultContent


class ChatHistoryManager:
    def __init__(self) -> None:
        # Holds, per session, a dict of the hash of the last user message to
        # any tool call records for tool calls that immediately follow it, indexed
        # by the call ID.
        self._session_id_to_tool_call_records: dict[
            str, dict[int, dict[str, ToolCallRecord]]
        ] = {}

    def get_chat_history(
        self,
        session_id: str | None,
        request_prompt: str,
        request_history: list[ChatMessageContent],
        system_message: str,
    ) -> ChatHistory:
        history = ChatHistory()

        history.add_system_message(system_message)

        for request_history_index, message in enumerate(request_history or []):
            metadata = {"request_history_index": request_history_index}
            if message.participant == "user":
                history.add_user_message(message.content, metadata=metadata)

                # If we've recorded tool calls after this user message,
                # add them to the history.
                if session_id in self._session_id_to_tool_call_records and (
                    request_history_index in self._session_id_to_tool_call_records[session_id]
                ):
                    for record in self._session_id_to_tool_call_records[session_id][
                        request_history_index
                    ].values():
                        history.add_tool_message([record.call])
                        history.add_tool_message([record.result])
            else:
                history.add_assistant_message(message.content, metadata=metadata)

        # Add prompt as last user input
        history.add_user_message(
            request_prompt, metadata={"request_history_index": len(request_history)}
        )

        return history

    def add_tool_call_record(
        self,
        session_id: str,
        last_user_message: SKChatMessageContent,
        call: FunctionCallContent,
        result: FunctionResultContent,
    ) -> None:
        """Add a tool call record to the chat history.

        Avoids adding duplicates by checking if the call ID already exists in the
        history for the last user message.

        Args:
            session_id (str): The session ID.
            last_user_message (str): The last user message. This will be used to key
                the placement in the chat history.
            call (FunctionCallContent): The function call content.
            result (FunctionResultContent): The function result content.
        """
        if "request_history_index" not in last_user_message.metadata:
            return
        request_history_index = (
            last_user_message.metadata.get("request_history_index")
            if last_user_message.metadata
            else None
        )
        if request_history_index is None:
            return
        tool_call_record = ToolCallRecord(call=call, result=result)
        if session_id not in self._session_id_to_tool_call_records:
            self._session_id_to_tool_call_records[session_id] = {}
        if request_history_index not in self._session_id_to_tool_call_records[session_id]:
            self._session_id_to_tool_call_records[session_id][request_history_index] = {}
        if (
            result.id
            not in self._session_id_to_tool_call_records[session_id][request_history_index]
        ):
            self._session_id_to_tool_call_records[session_id][request_history_index][
                result.id
            ] = tool_call_record
