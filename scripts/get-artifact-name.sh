#!/bin/bash
# Arguments: $1 = os, $2 = version
os="$1"
version="$2"
artifact=""

if [[ "$os" == "windows-latest" ]]; then
    artifact="pgsqltoolsservice-win-x64-${version}.zip"
elif [[ "$os" == *"macos"* ]]; then
    # For macOS assume we check architecture at runtime
    if [[ "$os" == "macos-13" || "$os" == "macos-latest" ]]; then
        if [[ "$(uname -m)" == "arm64" ]]; then
            artifact="pgsqltoolsservice-osx-arm64-${version}.tar.gz"
        else
            artifact="pgsqltoolsservice-osx-${version}.tar.gz"
        fi
    fi
elif [[ "$os" == *"ubuntu"* ]]; then
    # For Linux, check architecture
    if [[ "$(uname -m)" == "aarch64" ]]; then
        artifact="pgsqltoolsservice-linux-arm64-${version}.tar.gz"
    else
        artifact="pgsqltoolsservice-linux-x64-${version}.tar.gz"
    fi
fi

echo "${artifact}"
