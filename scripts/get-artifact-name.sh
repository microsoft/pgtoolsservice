#!/bin/bash

# This script is used to get the artifact name based on the operating system.
# This runs as part of the GitHub Actions workflow.

# Arguments: $1 = os
os="$1"
artifact=""

if [[ "$os" == "windows-2022" ]]; then
    artifact="pgsqltoolsservice-win-x64.zip"
elif [[ "$os" == "macos-13" ]]; then
    artifact="pgsqltoolsservice-osx.tar.gz"
elif [[ "$os" == "macos-14" ]]; then
    artifact="pgsqltoolsservice-osx-arm64.tar.gz"
elif [[ "$os" == "ubuntu-20.04" ]]; then
    artifact="pgsqltoolsservice-linux-x64.tar.gz"
elif [[ "$os" == "ubuntu-22.04-arm" ]]; then
    artifact="pgsqltoolsservice-linux-arm64.tar.gz"
else
    echo "Unknown operating system: $os"
    exit 1
fi

echo "${artifact}"
