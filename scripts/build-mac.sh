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
python3 setup.py bdist_mac

# Compress mysqltoolsservice folder
cd $pwd/build

# TODO: Remove this fix done for openssl libraries need to be copied manually in lib folder in mac
cp mysqltoolsservice/lib* mysqltoolsservice/lib/.

if [ "$1" = arm64 ]
then
    tar -cvzf mysqltoolsservice-osx-arm64.tar.gz mysqltoolsservice
else
    tar -cvzf mysqltoolsservice-osx.tar.gz mysqltoolsservice
fi

# Restore the old PYTHONPATH and move back to the original directory
cd $pwd
PYTHONPATH=$old_pythonpath

# Pass arm64 param to build for arm architecture else build will be for other intel arch