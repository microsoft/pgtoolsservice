from semantic_kernel import Kernel

from ossdbtoolsservice.chat.plugin.topic_documentation import TopicDocumentation


class PGTSChatPlugin:
    """Plugin base class"""

    def __init__(
        self,
        name: str,
        description: str,
        topic_documentation: list[TopicDocumentation] | None = None,
    ) -> None:
        self._name = name
        self._description = description
        self._topic_documentation = topic_documentation or []

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def topic_documentation(self) -> list[TopicDocumentation]:
        return self._topic_documentation

    def add_to(self, kernel: Kernel) -> None:
        kernel.add_plugin(self, plugin_name=self.name, description=self.description)
