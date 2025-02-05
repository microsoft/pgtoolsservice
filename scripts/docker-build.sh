#!/bin/bash

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Parse arguments
while getopts "v:" opt; do
    case "$opt" in
        v)
            BuildVersion="$OPTARG"
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

# Set BuildVersion to the current date and time if not provided
if [ -z "$BuildVersion" ]; then
    BuildVersion=$(date +"%Y-%m-%d-%H-%M-%S")
fi

# Print the generated BuildVersion
echo "BuildVersion: $BuildVersion"

# Save the current directory and the script's directory, since build must be run from the project root
pwd=$(pwd)
dirname=$(dirname "$0")
cd "$dirname/.."

# Build the docker image
docker build --progress=plain -t ossdbtoolsservice:$BuildVersion .

# Restore the original directory
cd "$pwd"
