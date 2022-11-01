#!/bin/sh

# Save the current directory and the script's directory, since build must be run from the project root
pwd=$(pwd)
dirname=$(dirname $0)

# Back up the old PYTHONPATH so it can be restored later
old_pythonpath=$PYTHONPATH

# Download dotnet install script
wget https://dot.net/v1/dotnet-install.sh -O $dirname/dotnet-install.sh

# Build the program
chmod +x $dirname/dotnet-install.sh
$dirname/dotnet-install.sh --install-dir $pwd/ossdbtoolsservice/dotnet-connector-deps/dotnet-deps --runtime dotnet

cd $dirname/..
PYTHONPATH=
pip3 install -r requirements.txt
python3 setup.py build

# Compress mysqltoolsservice folder
cd $pwd/build
if [ "$1" = ubuntu22 ]
then
    tar -cvzf mysqltoolsservice-ubuntu22-x64.tar.gz mysqltoolsservice
else
    tar -cvzf mysqltoolsservice-linux-x64.tar.gz mysqltoolsservice
fi

# Restore the old PYTHONPATH and move back to the original directory
cd $pwd
PYTHONPATH=$old_pythonpath

# Pass ubuntu22 param to build for Ubuntu22 else build will be for other linux distribution