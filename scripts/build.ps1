# Save the current directory and the script's directory, since build must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot

# Back up the old PYTHONPATH so it can be restored later
$oldPythonpath=$Env:PYTHONPATH

# Download dotnet install script
Invoke-WebRequest -Uri https://dot.net/v1/dotnet-install.ps1 -OutFile $scriptloc/dotnet-install.ps1

# Build the program
Unblock-File -Path $scriptloc/dotnet-install.ps1
& $scriptloc/dotnet-install.ps1 -InstallDir $curloc/ossdbtoolsservice/dotnet-connector-deps/dotnet-deps -Runtime dotnet

Set-Location $scriptloc/..
$Env:PYTHONPATH = ""
pip3 install -r requirements.txt
python setup.py build

# Compress mysqltoolsservice folder
Set-Location $curloc/build
Compress-Archive -LiteralPath mysqltoolsservice -DestinationPath mysqltoolsservice-win-x64 -Force

# Restore the old PYTHONPATH and move back to the original directory
Set-Location $curloc
$Env:PYTHONPATH = $oldPythonpath