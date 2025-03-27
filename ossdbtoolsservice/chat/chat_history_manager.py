from dataclasses import dataclass

from semantic_kernel.contents import ChatHistory, FunctionCallContent, FunctionResultContent

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

        for message in request_history or []:
            if message.participant == "user":
                history.add_user_message(message.content)

                # If we've recorded tool calls after this user message,
                # add them to the history.
                if session_id in self._session_id_to_tool_call_records:
                    message_hash = hash(message.content)
                    if message_hash in self._session_id_to_tool_call_records[session_id]:
                        for record in self._session_id_to_tool_call_records[session_id][
                            message_hash
                        ].values():
                            history.add_tool_message([record.call])
                            history.add_tool_message([record.result])
            else:
                history.add_assistant_message(message.content)

        # Add prompt as last user input
        history.add_user_message(request_prompt)

        return history

    def add_tool_call_record(
        self,
        session_id: str,
        last_user_message: str,
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
        tool_call_record = ToolCallRecord(call=call, result=result)
        message_hash = hash(last_user_message)
        if session_id not in self._session_id_to_tool_call_records:
            self._session_id_to_tool_call_records[session_id] = {}
        if message_hash not in self._session_id_to_tool_call_records[session_id]:
            self._session_id_to_tool_call_records[session_id][message_hash] = {}
        if result.id not in self._session_id_to_tool_call_records[session_id][message_hash]:
            self._session_id_to_tool_call_records[session_id][message_hash][result.id] = (
                tool_call_record
            )
