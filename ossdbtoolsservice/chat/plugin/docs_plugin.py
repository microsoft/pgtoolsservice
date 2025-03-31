from logging import Logger
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.functions import KernelFunction, kernel_function

from ossdbtoolsservice.chat.constants import GET_DOCS_FUNCTION_NAME
from ossdbtoolsservice.chat.messages import (
    CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
    CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
    ChatFunctionCallErrorNotificationParams,
    ChatFunctionCallNotificationParams,
)
from ossdbtoolsservice.chat.plugin.plugin_base import PGTSChatPlugin
from ossdbtoolsservice.chat.plugin.topic_documentation import TopicDocumentation
from ossdbtoolsservice.hosting.context import RequestContext


class DocsPlugin(PGTSChatPlugin):
    """DocsPlugin."""

    topic_documents: dict[str, TopicDocumentation] = {}

    def __init__(
        self,
        request_context: RequestContext,
        chat_id: str,
        logger: Logger | None,
    ) -> None:
        self._request_context = request_context
        self._chat_id = chat_id
        self._logger = logger

        super().__init__(
            name="DocumentationFetch",
            description="A plugin for fetching documentation on various topics.",
        )

    def add_topic_documentation(self, doc: TopicDocumentation) -> None:
        """Add topic documentation."""
        self.topic_documents[doc.topic] = doc

    def add_to(self, kernel: Kernel) -> None:
        """Override this method to generate dynamic kernel functions."""

        kernel.add_plugin(
            {"get_docs_for_topic": self._create_docs_kernel_function()},
            plugin_name=self.name,
            description=self.description,
        )

    def _create_docs_kernel_function(self) -> KernelFunction:
        """Create a kernel function for the documentation."""

        description = (
            "Fetches documentation on various topics. Below are the available topics:\n"
        )
        for doc in self.topic_documents.values():
            description += f"- {doc.topic}: {doc.description_for_tool}\n"

        @kernel_function(
            name=GET_DOCS_FUNCTION_NAME,
            description=description,
        )
        def get_doc(topic: Annotated[str, "The topic to get documentation for."]) -> str:
            """Get documentation for a topic."""
            self._request_context.send_notification(
                CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
                ChatFunctionCallNotificationParams(
                    chat_id=self._chat_id,
                    function_name=GET_DOCS_FUNCTION_NAME,
                    function_args={"topic": topic},
                    message=f"Checking docs about {topic} 📖...",
                ),
            )

            doc = self.topic_documents.get(topic)
            if not doc:
                if self._logger:
                    self._logger.warning(
                        "Docs Chat Plugin: "
                        f"No documentation found for requested topic: {topic}"
                    )
                return (
                    f"No documentation found for topic: {topic}. "
                    "Please select a topic from the description."
                )
            if self._logger:
                self._logger.info(f"Docs Chat Plugin: Fetching documentation for {doc.topic}")

            try:
                return doc.get_text()
            except Exception as e:
                if self._logger:
                    self._logger.exception(e)
                    self._logger.error(
                        f"Docs Chat Plugin: Error fetching documentation for {doc.topic}: {e}"
                    )
                self._request_context.send_notification(
                    CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
                    ChatFunctionCallErrorNotificationParams(
                        chat_id=self._chat_id,
                        function_name=GET_DOCS_FUNCTION_NAME,
                    ),
                )
                return f"Error fetching documentation for {doc.topic}: {e}"

        return get_doc
