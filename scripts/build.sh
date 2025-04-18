#!/bin/bash

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Save the current directory and the script's directory, since build must be run from the project root
pwd=$(pwd)
dirname=$(dirname "$0")

# Back up the old PYTHONPATH so it can be restored later
old_pythonpath=$PYTHONPATH

# Pass in "webserver" if building the webserver version of the service
ARG=$1

# Build the program
cd "$dirname/.."
export PYTHONPATH=""
pip3 install -e .[dev]
pyinstaller ossdbtoolsservice_main.spec

# Create folder pgsqltoolsservice in dist folder
mkdir -p "./dist/pgsqltoolsservice"

# Move the contents in the dist folder to pgsqltoolsservice folder
find "./dist" -maxdepth 1 -type f -exec mv {} "./dist/pgsqltoolsservice" \;

# Only copy the development SSL certificate and config file if "webserver" argument is passed
if [ "$ARG" == "webserver" ]; then
    # Copy the development SSL certificate to the dist folder
    mkdir -p "./dist/pgsqltoolsservice/ssl"
    cp "./ssl/cert.pem" "./dist/pgsqltoolsservice/ssl/"
    cp "./ssl/key.pem" "./dist/pgsqltoolsservice/ssl/"

    # Copy the pgsqltoolsservice config file to the dist folder
    cp "./config.ini" "./dist/pgsqltoolsservice/"
fi

# Check the current operating system and copy the correct pgsqltoolsservice
if [[ "$(uname)" == "Darwin" ]]; then
    mkdir -p "./dist/pgsqltoolsservice/pg_exes/mac"
    cp -R "./ossdbtoolsservice/pg_exes/mac" "./dist/pgsqltoolsservice/pg_exes/"
elif [[ "$(uname)" == "Linux" ]]; then
    mkdir -p "./dist/pgsqltoolsservice/pg_exes/linux"
    cp -R "./ossdbtoolsservice/pg_exes/linux" "./dist/pgsqltoolsservice/pg_exes/"
fi

# Restore the old PYTHONPATH and move back to the original directory
cd "$pwd"
export PYTHONPATH="$old_pythonpath"
