# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Annotated

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)

from .messages import VSCodeLanguageModelChatTool


class VSCodeChatPromptExecutionSettings(PromptExecutionSettings):
    tools: Annotated[
        list[VSCodeLanguageModelChatTool] | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None
