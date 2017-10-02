# Save the current directory and the script's directory, since build must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot

# Run autopep8
Set-Location $scriptloc/..
autopep8 --in-place --aggressive --aggressive --max-line-length 160 -r .

# Move back to the original directory
Set-Location $curloc
