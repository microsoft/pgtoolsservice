# Summary
DTO Generator is a utility used to parse [pgtoolsservice](../ossdbtoolsservice/) and emit DTO objects, in the form of JSON Schema, for parameter and message classes registered in `IncomingMessageConfiguration` and `OutgoingMessageRegistration` classes respectively. 

# Running the Tool
1. Run the `run_dto_generator.ps1` or `run_dto_generator.sh` script from this folder (depending on your environment)

# Updating DTO Objects
To update the DTO objects in webserver_client:
2. Run tool as above
3. Run the `import_dto.ps1` or `import_dto.sh` script from [webserver_client](../webserver_client/) folder (depending on your environment)