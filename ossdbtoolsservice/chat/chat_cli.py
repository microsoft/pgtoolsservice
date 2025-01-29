import asyncio

import click

from rich.console import Console
from rich.markdown import Markdown
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.connectors.memory.postgres import PostgresSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

from .entra_connection import AsyncEntraConnection
from .plugin.postgres_plugin import PostgresPlugin


async def chat_with_postgresql(env_file_path: str = ".env") -> None:
    # Create a Kernel
    kernel = Kernel()
    console = Console()

    # Add the AzureChatCompletion service, which will be used to generate completions for the chat.
    chat_completion = AzureChatCompletion(service_id="chat", deployment_name="gpt-4o")
    kernel.add_service(chat_completion)

    # Create a connection pool using the PostgresSettings from PostgresVectorStore
    settings = PostgresSettings.create(env_file_path=env_file_path)
    connection_pool = await settings.create_connection_pool(
        connection_class=AsyncEntraConnection
    )
    async with connection_pool:
        # Add a kernel function that gives the database schema
        PostgresPlugin(connection_pool=connection_pool, console=console).add_to(kernel)

        chat_function = kernel.add_function(
            prompt="{{$chat_history}}{{$user_input}}",
            plugin_name="ChatBot",
            function_name="Chat",
        )

        # we set the function choice to Auto, so that the LLM can choose the correct function to call.
        # and we exclude the ChatBot plugin, so that it does not call itself.
        # this means that it has access to 2 functions, that were defined above.
        execution_settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(
                filters={"excluded_plugins": ["ChatBot"]}
            ),
            service_id="chat",
            max_tokens=7000,
            temperature=0.7,
            top_p=0.8,
        )

        history = ChatHistory()
        system_message = """
        You are a chat bot. Your name is Dumbo and
        you have one goal: help people work with their PostgreSQL database.
        Assume that questions about the database schema, tables, columns, and data etc are
        all referring to the user's specific database, and fetch the database context
        before providing an answer.
        If the user's inquiry can be aided by a SQL script, you will provide it in the response.
        You utilize the specific PostgreSQL database context the user has access to whenever possible.
        If the user does not specify a specific schema to work with, you will default to the 'public' schema.
        You are able to execute read-only SQL queries against the user's database. You can execute read-only
         statements arbitrarily.
        For any statement that will modify the database, you should always
        present the query to the user before executing it. Present the query with a name that the user can reference
         when confirming that it should be executed. The user MUST confirm the query BY NAME before it is
        executed.
        """
        history.add_system_message(system_message)
        history.add_user_message("Hi there, who are you?")
        history.add_assistant_message(
            "I am Dumbo, the PostgreSQL chat bot. I'm here to help you work with your PostgreSQL database."
        )

        arguments = KernelArguments(settings=execution_settings)

        console.print(
            """[italic]Welcome to the PostgreSQL chat bot! Type 'exit' to exit the chat.[/italic]\n"""
        )

        chatting = True
        while chatting:
            try:
                user_input = console.input("[bold]User :>[/bold] ")
                print()
            except KeyboardInterrupt:
                print("\n\nExiting chat...")
                return
            except EOFError:
                print("\n\nExiting chat...")
                return

            if user_input == "exit":
                print("\n\nExiting chat...")
                return
            arguments["user_input"] = user_input
            arguments["chat_history"] = history
            print(f"🐘 :>")
            result = await kernel.invoke(chat_function, arguments=arguments)
            print()
            console.print(Markdown(str(result)))
            print()
            history.add_user_message(user_input)
            history.add_assistant_message(str(result))
            chatting = True


@click.group()
def cli() -> None:
    """PostgreSQL Copilot."""
    pass


@cli.command()
def chat() -> None:
    """Chat with your database."""
    asyncio.run(chat_with_postgresql())


if __name__ == "__main__":
    cli()
