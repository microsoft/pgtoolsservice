# Stage 1: Build the executable using PyInstaller
FROM python:3.8-slim AS builder

# Set the working directory in the container
WORKDIR /src

# Install binutils for objdump
RUN apt-get update && apt-get install -y binutils

# Copy the current directory contents into the container at /app
COPY scripts /src/scripts
COPY ossdbtoolsservice /src/ossdbtoolsservice
COPY pgsmo /src/pgsmo
COPY smo /src/smo
COPY ssl /src/ssl
COPY config.ini requirements.txt ossdbtoolsservice_main.spec /src/

# Run the build script
RUN scripts/build.sh

# Stage 2: Package the built executable into a minimal Docker container
FROM debian:latest

# Set the working directory in the container
WORKDIR /app

# Copy the built executable from the builder stage
COPY --from=builder /src/dist/pgsqltoolsservice /app

# Set the appropriate permissions
RUN chmod -R +x /app

# Specify the command to run the executable
CMD ["/app/ossdbtoolsservice_main", "--enable-web-server", "--console-logging"]