# Summary
Webserver Client is a sample website used to interact with the [pgtoolsservice](../ossdbtoolsservice/) running in webserver mode `--enable-web-server`
Users can test out request and view responses in the browser.

# Setting Up the Environment

From the `webserver_client` directory:
1. Run `npm install` to install dependencies.
2. Run `npx webpack` to compile and package TypeScript.
3. Run `npx serve .` to start the local client server.

***Note:*** *To use this client the pgtoolsservice must NOT be started with `--disable-keep-alive`*

# Updating DTO Objects
To update the DTO objects from the pgtoolservice:
1. Ensure you've set up the environment as above
2. Run the [DTO Generator](../dto_generator/)
3. Run the `import_dto.ps1` or `import_dto.sh` script from this folder (depending on your environment)