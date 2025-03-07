# Stage 1: Build the executable using PyInstaller
FROM mcr.microsoft.com/azurelinux/base/python:3.12

# Set the working directory in the container
WORKDIR /src

# Install binutils for objdump
RUN tdnf install -y binutils

# Copy the current directory contents into the container at /app
COPY scripts /src/scripts
COPY ossdbtoolsservice /src/ossdbtoolsservice
COPY pgsmo /src/pgsmo
COPY smo /src/smo
COPY ssl /src/ssl
COPY config.ini ossdbtoolsservice_main.spec /src/
COPY setup.cfg /src/
COPY pyproject.toml /src/

# Install pgtoolsservice
RUN pip3 install -e .

# Specify the command to run the executable
CMD ["python3", "/src/ossdbtoolsservice/ossdbtoolsservice_main_web.py", "--enable-web-server", "--console-logging",]