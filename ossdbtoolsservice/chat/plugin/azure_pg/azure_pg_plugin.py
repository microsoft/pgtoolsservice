import json
from logging import Logger
from pathlib import Path
from typing import Annotated

from azure.mgmt.postgresqlflexibleservers import PostgreSQLManagementClient
from azure.mgmt.postgresqlflexibleservers.models import ConfigurationForUpdate
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

from ossdbtoolsservice.az.static_token import StaticTokenCredential
from ossdbtoolsservice.chat.constants import (
    ADD_ALLOWED_EXTENSIONS_FUNC_NAME,
    AZURE_GET_BACKUP_INFO_FUNCTION_NAME,
    AZURE_GET_SERVER_INFO_FUNCTION_NAME,
    GET_ALLOWED_EXTENSIONS_FUNC_NAME,
)
from ossdbtoolsservice.chat.messages import (
    CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
    CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
    ChatFunctionCallErrorNotificationParams,
    ChatFunctionCallNotificationParams,
)
from ossdbtoolsservice.chat.plugin.plugin_base import PGTSChatPlugin
from ossdbtoolsservice.chat.plugin.topic_documentation import TopicDocumentation
from ossdbtoolsservice.hosting.context import RequestContext


class AzurePGPlugin(PGTSChatPlugin):
    def __init__(
        self,
        request_context: RequestContext,
        chat_id: str,
        subscription_id: str | None,
        resource_group: str | None,
        server_name: str | None,
        database_name: str | None,
        arm_token: str | None,
        logger: Logger | None,
    ) -> None:
        self.request_context = request_context
        self.chat_id = chat_id
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.server_name = server_name
        self.database_name = database_name
        self.arm_token = arm_token
        self.logger = logger

        super().__init__(
            name="AzurePostgreSQL",
            description="A plugin for interacting with Azure PostgreSQL databases.",
            topic_documentation=[
                TopicDocumentation.from_file(
                    topic="DiskANN",
                    description_for_tool="Documentation on the DiskANN algorithm and "
                    "extension for Azure PostgreSQL database.",
                    file_path=Path(__file__).parent / "diskann.md",
                ),
                TopicDocumentation.from_file(
                    topic="azure_ai extension",
                    description_for_tool="Documentation on how to create embeddings "
                    "using the azure_ai extension.",
                    file_path=Path(__file__).parent / "azure_ai.md",
                ),
            ],
        )

    def add_to(self, kernel: Kernel) -> None:
        super().add_to(kernel)

        # If we have all the required parameters, add the ARM plugin.
        if (
            self.subscription_id
            and self.resource_group
            and self.server_name
            and self.arm_token
        ):
            arm_plugin = AzurePGArmPlugin(
                request_context=self.request_context,
                chat_id=self.chat_id,
                subscription_id=self.subscription_id,
                resource_group=self.resource_group,
                server_name=self.server_name,
                arm_token=self.arm_token,
                logger=self.logger,
            )
            kernel.add_plugin(
                arm_plugin,
                plugin_name="AzurePGArmPlugin",
                description="A plugin for managing Azure PG Flexible Servers.",
            )


class AzurePGArmPlugin:
    def __init__(
        self,
        request_context: RequestContext,
        chat_id: str,
        subscription_id: str,
        resource_group: str,
        server_name: str,
        arm_token: str,
        logger: Logger | None,
    ) -> None:
        self.request_context = request_context
        self.chat_id = chat_id
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.server_name = server_name
        self.arm_token = arm_token
        self.logger = logger

    def get_server_name(self) -> str:
        """
        Get the server name from the Azure PostgreSQL configuration.
        Parses the server name from the *.postgresql.azure.com domain.
        """
        return self.server_name.split(".")[0]

    def get_client(self) -> PostgreSQLManagementClient:
        """
        Get the PostgreSQLManagementClient instance.
        """
        credential = StaticTokenCredential(self.arm_token)
        return PostgreSQLManagementClient(
            credential=credential, subscription_id=self.subscription_id
        )

    @kernel_function(
        name=AZURE_GET_SERVER_INFO_FUNCTION_NAME,
        description="Get information about an Azure PostgreSQL server.",
    )
    def get_azure_pg_server_info(
        self,
    ) -> Annotated[str, "A JSON object containing server information."]:
        """
        Get information about an Azure PostgreSQL server.
        """

        if self.logger:
            self.logger.info(" ... Fetching Azure PostgreSQL server information")

        self.request_context.send_notification(
            CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
            ChatFunctionCallNotificationParams(
                chat_id=self.chat_id,
                function_name=AZURE_GET_SERVER_INFO_FUNCTION_NAME,
                message="Fetching Azure PostgreSQL server information ☁️...",
            ),
        )

        try:
            client = self.get_client()

            server = client.servers.get(
                resource_group_name=self.resource_group, server_name=self.get_server_name()
            )
            sku = server.sku.as_dict() if server.sku else {}
            sku_info = {}
            sku_name = sku.get("name", "").upper()
            if sku_name:
                sku_vm = "_".join(sku_name.split("_")[1:])
                sku_info = SKU_INFO.get(sku_vm) or {}

            return json.dumps(
                {
                    "sku": {**sku, **sku_info},
                    "storage": server.storage.as_dict() if server.storage else None,
                }
            )
        except Exception as e:
            if self.logger:
                self.logger.exception(e)
                self.logger.error(f"Error fetching server info: {e}")
            self.request_context.send_notification(
                CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
                ChatFunctionCallErrorNotificationParams(
                    chat_id=self.chat_id,
                    function_name=AZURE_GET_SERVER_INFO_FUNCTION_NAME,
                ),
            )
            return "Error fetching server info: {e}"

    @kernel_function(
        name=GET_ALLOWED_EXTENSIONS_FUNC_NAME,
        description="Get allow list of extensions for an Azure PostgreSQL server.",
    )
    def get_azure_pg_allowed_extensions(
        self,
    ) -> Annotated[str, "A JSON object containing the list of allowed extensions."]:
        """
        Get the allow list of extensions for an Azure PostgreSQL server.
        """

        if self.logger:
            self.logger.info(" ... Fetching Azure PostgreSQL allowed extensions")

        self.request_context.send_notification(
            CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
            ChatFunctionCallNotificationParams(
                chat_id=self.chat_id,
                function_name=GET_ALLOWED_EXTENSIONS_FUNC_NAME,
                message="Fetching Azure PostgreSQL allowed extensions ☁️...",
            ),
        )

        try:
            client = self.get_client()

            config = client.configurations.get(
                resource_group_name=self.resource_group,
                server_name=self.get_server_name(),
                configuration_name="azure.extensions",
            )

            result: dict[str, list[str]] = {"allowed_extensions": [], "possible_values": []}
            if config.value:
                result["allowed_extensions"] = config.value.split(",")
            if config.allowed_values:
                result["possible_values"] = [
                    x
                    # azure sdk type issue, allowed values is 'never'
                    for x in config.allowed_values.split(",")  # type:ignore
                    if x
                ]

            return json.dumps(result)
        except Exception as e:
            if self.logger:
                self.logger.exception(e)
                self.logger.error(f"Error fetching allowed extensions: {e}")
            self.request_context.send_notification(
                CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
                ChatFunctionCallErrorNotificationParams(
                    chat_id=self.chat_id,
                    function_name=GET_ALLOWED_EXTENSIONS_FUNC_NAME,
                ),
            )
            return json.dumps(
                {
                    "error": f"Error fetching allowed extensions: {e}",
                }
            )

    @kernel_function(
        name=ADD_ALLOWED_EXTENSIONS_FUNC_NAME,
        description="Add extensions to the  allow list of extensions "
        "for an Azure PostgreSQL server.",
    )
    def add_azure_pg_allowed_extensions(
        self,
        new_allowed_extensions: Annotated[
            list[str],
            "A list of new allowed extensions. "
            f"Must be in the list of allowed values from {GET_ALLOWED_EXTENSIONS_FUNC_NAME}.",
        ],
    ) -> Annotated[str, "'success' or an error message."]:
        """
        Set the allow list of extensions for an Azure PostgreSQL server
        to include the new extensions.
        """

        if self.logger:
            self.logger.info(
                f"...Adding {','.join(new_allowed_extensions)} to "
                "Azure PostgreSQL allowed extensions"
            )

        self.request_context.send_notification(
            CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
            ChatFunctionCallNotificationParams(
                chat_id=self.chat_id,
                function_name=ADD_ALLOWED_EXTENSIONS_FUNC_NAME,
                message=f"Adding {','.join(new_allowed_extensions)} to "
                "Azure PostgreSQL allowed extensions ☁️...",
            ),
        )

        try:
            client = self.get_client()

            config = client.configurations.get(
                resource_group_name=self.resource_group,
                server_name=self.get_server_name(),
                configuration_name="azure.extensions",
            )

            current_values = config.value.split(",") if config.value else []
            allowed_values = config.allowed_values.split(",") if config.allowed_values else []
            not_allowed_extensions = []
            for new_extension in new_allowed_extensions:
                if new_extension not in allowed_values:
                    not_allowed_extensions.append(new_extension)
            if not_allowed_extensions:
                return (
                    f"Error: Extensions {', '.join(not_allowed_extensions)} are not able to "
                    "be set in the allow list. Did you check the list of possible values "
                    f"from {GET_ALLOWED_EXTENSIONS_FUNC_NAME}?"
                )

            new_allowed_extensions = list(set(current_values + new_allowed_extensions))

            config_for_update = ConfigurationForUpdate(
                value=",".join(new_allowed_extensions), source="user-override"
            )

            client.configurations.begin_update(
                resource_group_name=self.resource_group,
                server_name=self.get_server_name(),
                configuration_name="azure.extensions",
                parameters=config_for_update,
            ).result(timeout=60 * 3)

            return "success"
        except Exception as e:
            if self.logger:
                self.logger.exception(e)
                self.logger.error(f"Error setting allowed extensions: {e}")
            self.request_context.send_notification(
                CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
                ChatFunctionCallErrorNotificationParams(
                    chat_id=self.chat_id,
                    function_name=ADD_ALLOWED_EXTENSIONS_FUNC_NAME,
                ),
            )
            return f"Error: Error fetching allowed extensions: {e}"

    @kernel_function(
        name=AZURE_GET_BACKUP_INFO_FUNCTION_NAME,
        description="Get information about the backups that an Azure PostgreSQL server has.",
    )
    def get_azure_pg_backups_info(
        self,
    ) -> Annotated[
        list[str], "A list of JSON object containing information about backups of the server."
    ]:
        """
        Get information about backups for an Azure PostgreSQL server.
        """
        if self.logger:
            self.logger.info(" ... Fetching Azure PostgreSQL backup information")

        self.request_context.send_notification(
            CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
            ChatFunctionCallNotificationParams(
                chat_id=self.chat_id,
                function_name=AZURE_GET_BACKUP_INFO_FUNCTION_NAME,
                message="Fetching Azure PostgreSQL backup information ☁️...",
            ),
        )

        try:
            client = self.get_client()

            backups = client.backups.list_by_server(
                resource_group_name=self.resource_group,
                server_name=self.get_server_name(),
            )

            backup_dicts = []
            for backup in backups:
                backup_dict = backup.as_dict()
                if backup.completed_time:
                    backup_dict["completed_time"] = (
                        backup.completed_time.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
                    )
                backup_dicts.append(backup_dict)

            return [json.dumps(backup_dict) for backup_dict in backup_dicts]
        except Exception as e:
            if self.logger:
                self.logger.exception(e)
                self.logger.error(f"Error fetching backups: {e}")
            self.request_context.send_notification(
                CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
                ChatFunctionCallErrorNotificationParams(
                    chat_id=self.chat_id,
                    function_name=AZURE_GET_BACKUP_INFO_FUNCTION_NAME,
                ),
            )
            return [f"Error fetching backups: {e}"]


# TODO: Where to put this?
SKU_INFO = {
    k.upper(): v
    for (k, v) in {
        "B1ms": {
            "vCores": 1,
            "Memory size": "2 GiB",
            "Maximum supported IOPS": 640,
            "Maximum supported I/O bandwidth": "10 MiB/sec",
        },
        "B2s": {
            "vCores": 2,
            "Memory size": "4 GiB",
            "Maximum supported IOPS": 1280,
            "Maximum supported I/O bandwidth": "15 MiB/sec",
        },
        "B2ms": {
            "vCores": 2,
            "Memory size": "8 GiB",
            "Maximum supported IOPS": 1920,
            "Maximum supported I/O bandwidth": "22.5 MiB/sec",
        },
        "B4ms": {
            "vCores": 4,
            "Memory size": "16 GiB",
            "Maximum supported IOPS": 2880,
            "Maximum supported I/O bandwidth": "35 MiB/sec",
        },
        "B8ms": {
            "vCores": 8,
            "Memory size": "32 GiB",
            "Maximum supported IOPS": 4320,
            "Maximum supported I/O bandwidth": "50 MiB/sec",
        },
        "B12ms": {
            "vCores": 12,
            "Memory size": "48 GiB",
            "Maximum supported IOPS": 4320,
            "Maximum supported I/O bandwidth": "50 MiB/sec",
        },
        "B16ms": {
            "vCores": 16,
            "Memory size": "64 GiB",
            "Maximum supported IOPS": 4320,
            "Maximum supported I/O bandwidth": "50 MiB/sec",
        },
        "B20ms": {
            "vCores": 20,
            "Memory size": "80 GiB",
            "Maximum supported IOPS": 4320,
            "Maximum supported I/O bandwidth": "50 MiB/sec",
        },
        "D2s_v3": {
            "vCores": 2,
            "Memory size": "8 GiB",
            "Maximum supported IOPS": 3200,
            "Maximum supported I/O bandwidth": "48 MiB/sec",
        },
        "D2ds_v4": {
            "vCores": 2,
            "Memory size": "8 GiB",
            "Maximum supported IOPS": 3200,
            "Maximum supported I/O bandwidth": "48 MiB/sec",
        },
        "D2ds_v5": {
            "vCores": 2,
            "Memory size": "8 GiB",
            "Maximum supported IOPS": 3750,
            "Maximum supported I/O bandwidth": "85 MiB/sec",
        },
        "D2ads_v5": {
            "vCores": 2,
            "Memory size": "8 GiB",
            "Maximum supported IOPS": 3750,
            "Maximum supported I/O bandwidth": "85 MiB/sec",
        },
        "D4s_v3": {
            "vCores": 4,
            "Memory size": "16 GiB",
            "Maximum supported IOPS": 6400,
            "Maximum supported I/O bandwidth": "96 MiB/sec",
        },
        "D4ds_v4": {
            "vCores": 4,
            "Memory size": "16 GiB",
            "Maximum supported IOPS": 6400,
            "Maximum supported I/O bandwidth": "96 MiB/sec",
        },
        "D4ds_v5": {
            "vCores": 4,
            "Memory size": "16 GiB",
            "Maximum supported IOPS": 6400,
            "Maximum supported I/O bandwidth": "145 MiB/sec",
        },
        "D4ads_v5": {
            "vCores": 4,
            "Memory size": "16 GiB",
            "Maximum supported IOPS": 6400,
            "Maximum supported I/O bandwidth": "145 MiB/sec",
        },
        "D8s_v3": {
            "vCores": 8,
            "Memory size": "32 GiB",
            "Maximum supported IOPS": 12800,
            "Maximum supported I/O bandwidth": "192 MiB/sec",
        },
        "D8ds_v4": {
            "vCores": 8,
            "Memory size": "32 GiB",
            "Maximum supported IOPS": 12800,
            "Maximum supported I/O bandwidth": "192 MiB/sec",
        },
        "D8ds_v5": {
            "vCores": 8,
            "Memory size": "32 GiB",
            "Maximum supported IOPS": 12800,
            "Maximum supported I/O bandwidth": "290 MiB/sec",
        },
        "D8ads_v5": {
            "vCores": 8,
            "Memory size": "32 GiB",
            "Maximum supported IOPS": 12800,
            "Maximum supported I/O bandwidth": "290 MiB/sec",
        },
        "D16s_v3": {
            "vCores": 16,
            "Memory size": "64 GiB",
            "Maximum supported IOPS": 25600,
            "Maximum supported I/O bandwidth": "384 MiB/sec",
        },
        "D16ds_v4": {
            "vCores": 16,
            "Memory size": "64 GiB",
            "Maximum supported IOPS": 25600,
            "Maximum supported I/O bandwidth": "384 MiB/sec",
        },
        "D16ds_v5": {
            "vCores": 16,
            "Memory size": "64 GiB",
            "Maximum supported IOPS": 25600,
            "Maximum supported I/O bandwidth": "600 MiB/sec",
        },
        "D32s_v3": {
            "vCores": 32,
            "Memory size": "128 GiB",
            "Maximum supported IOPS": 51200,
            "Maximum supported I/O bandwidth": "768 MiB/sec",
        },
        "D32ds_v4": {
            "vCores": 32,
            "Memory size": "128 GiB",
            "Maximum supported IOPS": 51200,
            "Maximum supported I/O bandwidth": "768 MiB/sec",
        },
        "D32ds_v5": {
            "vCores": 32,
            "Memory size": "128 GiB",
            "Maximum supported IOPS": 51200,
            "Maximum supported I/O bandwidth": "865 MiB/sec",
        },
        "D32ads_v5": {
            "vCores": 32,
            "Memory size": "128 GiB",
            "Maximum supported IOPS": 51200,
            "Maximum supported I/O bandwidth": "865 MiB/sec",
        },
        "D48s_v3": {
            "vCores": 48,
            "Memory size": "192 GiB",
            "Maximum supported IOPS": 76800,
            "Maximum supported I/O bandwidth": "1152 MiB/sec",
        },
        "D48ds_v4": {
            "vCores": 48,
            "Memory size": "192 GiB",
            "Maximum supported IOPS": 76800,
            "Maximum supported I/O bandwidth": "1152 MiB/sec",
        },
        "D48ds_v5": {
            "vCores": 48,
            "Memory size": "192 GiB",
            "Maximum supported IOPS": 76800,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "D48ads_v5": {
            "vCores": 48,
            "Memory size": "192 GiB",
            "Maximum supported IOPS": 76800,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "D64s_v3": {
            "vCores": 64,
            "Memory size": "256 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "D64ds_v4": {
            "vCores": 64,
            "Memory size": "256 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "D64ds_v5": {
            "vCores": 64,
            "Memory size": "256 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "D64ads_v5": {
            "vCores": 64,
            "Memory size": "256 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "D96ds_v5": {
            "vCores": 96,
            "Memory size": "384 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "D96ads_v5": {
            "vCores": 96,
            "Memory size": "384 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "E2s_v3": {
            "vCores": 2,
            "Memory size": "16 GiB",
            "Maximum supported IOPS": 3200,
            "Maximum supported I/O bandwidth": "48 MiB/sec",
        },
        "E2ds_v4": {
            "vCores": 2,
            "Memory size": "16 GiB",
            "Maximum supported IOPS": 3200,
            "Maximum supported I/O bandwidth": "48 MiB/sec",
        },
        "E2ds_v5": {
            "vCores": 2,
            "Memory size": "16 GiB",
            "Maximum supported IOPS": 3200,
            "Maximum supported I/O bandwidth": "85 MiB/sec",
        },
        "E2ads_v5": {
            "vCores": 2,
            "Memory size": "16 GiB",
            "Maximum supported IOPS": 3200,
            "Maximum supported I/O bandwidth": "85 MiB/sec",
        },
        "E4s_v3": {
            "vCores": 4,
            "Memory size": "32 GiB",
            "Maximum supported IOPS": 6400,
            "Maximum supported I/O bandwidth": "96 MiB/sec",
        },
        "E4ds_v4": {
            "vCores": 4,
            "Memory size": "32 GiB",
            "Maximum supported IOPS": 6400,
            "Maximum supported I/O bandwidth": "96 MiB/sec",
        },
        "E4ds_v5": {
            "vCores": 4,
            "Memory size": "32 GiB",
            "Maximum supported IOPS": 6400,
            "Maximum supported I/O bandwidth": "145 MiB/sec",
        },
        "E4ads_v5": {
            "vCores": 4,
            "Memory size": "32 GiB",
            "Maximum supported IOPS": 6400,
            "Maximum supported I/O bandwidth": "145 MiB/sec",
        },
        "E8s_v3": {
            "vCores": 8,
            "Memory size": "64 GiB",
            "Maximum supported IOPS": 12800,
            "Maximum supported I/O bandwidth": "192 MiB/sec",
        },
        "E8ds_v4": {
            "vCores": 8,
            "Memory size": "64 GiB",
            "Maximum supported IOPS": 12800,
            "Maximum supported I/O bandwidth": "192 MiB/sec",
        },
        "E8ds_v5": {
            "vCores": 8,
            "Memory size": "64 GiB",
            "Maximum supported IOPS": 12800,
            "Maximum supported I/O bandwidth": "290 MiB/sec",
        },
        "E8ads_v5": {
            "vCores": 8,
            "Memory size": "64 GiB",
            "Maximum supported IOPS": 12800,
            "Maximum supported I/O bandwidth": "290 MiB/sec",
        },
        "E16s_v3": {
            "vCores": 16,
            "Memory size": "128 GiB",
            "Maximum supported IOPS": 25600,
            "Maximum supported I/O bandwidth": "384 MiB/sec",
        },
        "E16ds_v4": {
            "vCores": 16,
            "Memory size": "128 GiB",
            "Maximum supported IOPS": 25600,
            "Maximum supported I/O bandwidth": "384 MiB/sec",
        },
        "E16ds_v5": {
            "vCores": 16,
            "Memory size": "128 GiB",
            "Maximum supported IOPS": 25600,
            "Maximum supported I/O bandwidth": "600 MiB/sec",
        },
        "E20ds_v4": {
            "vCores": 20,
            "Memory size": "160 GiB",
            "Maximum supported IOPS": 32000,
            "Maximum supported I/O bandwidth": "480 MiB/sec",
        },
        "E20ds_v5": {
            "vCores": 20,
            "Memory size": "160 GiB",
            "Maximum supported IOPS": 32000,
            "Maximum supported I/O bandwidth": "750 MiB/sec",
        },
        "E20ads_v5": {
            "vCores": 20,
            "Memory size": "160 GiB",
            "Maximum supported IOPS": 32000,
            "Maximum supported I/O bandwidth": "750 MiB/sec",
        },
        "E32s_v3": {
            "vCores": 32,
            "Memory size": "256 GiB",
            "Maximum supported IOPS": 51200,
            "Maximum supported I/O bandwidth": "768 MiB/sec",
        },
        "E32ds_v4": {
            "vCores": 32,
            "Memory size": "256 GiB",
            "Maximum supported IOPS": 51200,
            "Maximum supported I/O bandwidth": "768 MiB/sec",
        },
        "E32ds_v5": {
            "vCores": 32,
            "Memory size": "256 GiB",
            "Maximum supported IOPS": 51200,
            "Maximum supported I/O bandwidth": "865 MiB/sec",
        },
        "E32ads_v5": {
            "vCores": 32,
            "Memory size": "256 GiB",
            "Maximum supported IOPS": 51200,
            "Maximum supported I/O bandwidth": "865 MiB/sec",
        },
        "E48s_v3": {
            "vCores": 48,
            "Memory size": "384 GiB",
            "Maximum supported IOPS": 76800,
            "Maximum supported I/O bandwidth": "1152 MiB/sec",
        },
        "E48ds_v4": {
            "vCores": 48,
            "Memory size": "384 GiB",
            "Maximum supported IOPS": 76800,
            "Maximum supported I/O bandwidth": "1152 MiB/sec",
        },
        "E48ds_v5": {
            "vCores": 48,
            "Memory size": "384 GiB",
            "Maximum supported IOPS": 76800,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "E48ads_v5": {
            "vCores": 48,
            "Memory size": "384 GiB",
            "Maximum supported IOPS": 76800,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "E64s_v3": {
            "vCores": 64,
            "Memory size": "432 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "E64ds_v4": {
            "vCores": 64,
            "Memory size": "432 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "E64ds_v5": {
            "vCores": 64,
            "Memory size": "512 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "E64ads_v4": {
            "vCores": 64,
            "Memory size": "512 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "E96ds_v5": {
            "vCores": 96,
            "Memory size": "672 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
        "E96ads_v5": {
            "vCores": 96,
            "Memory size": "672 GiB",
            "Maximum supported IOPS": 80000,
            "Maximum supported I/O bandwidth": "1200 MiB/sec",
        },
    }.items()
}
