from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ossdbtoolsservice.chat.prompts import template


@dataclass
class TopicDocumentation:
    """TopicDocumentation."""

    topic: str
    description_for_tool: str
    text: str | Callable[[], str]

    _cached_text: str | None = None

    def get_text(self) -> str:
        """Get the text."""
        if isinstance(self.text, str):
            return self.text
        if self._cached_text is None:
            self._cached_text = self.text()
        return self._cached_text

    @classmethod
    def from_file(
        cls, topic: str, description_for_tool: str, file_path: str | Path
    ) -> "TopicDocumentation":
        """Create a TopicDocumentation instance from a file."""
        return cls(
            topic, description_for_tool, lambda: Path(file_path).read_text(encoding="utf-8")
        )

    @classmethod
    def from_template(
        cls,
        topic: str,
        description_for_tool: str,
        template_path: str | Path,
        **kwargs: Any,
    ) -> "TopicDocumentation":
        """Create a TopicDocumentation instance from a template."""

        def read_template() -> str:
            template_text = Path(template_path).read_text(encoding="utf-8")
            return template(template_text, **kwargs)

        return cls(topic, description_for_tool, read_template)
