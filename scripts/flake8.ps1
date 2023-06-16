# Save the current directory and the script's directory, since build must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot

# Back up the old PYTHONPATH so it can be restored later
$oldPythonpath=$Env:PYTHONPATH

# Build the program
Set-Location $scriptloc/..
$Env:PYTHONPATH = ""
$errors = flake8 --max-line-length=160 --ignore W605,W503,W504 --builtins psycopg,ossdbtoolsservice,View ossdbtoolsservice tests pgsmo

if ($errors) {
    Write-Host "flake8 style check failed:"
    Write-Host $errors
    exit 1
}

# Restore the old PYTHONPATH and move back to the original directory
Set-Location $curloc
$Env:PYTHONPATH = $oldPythonpath
