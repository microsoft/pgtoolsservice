# Set error action so the script exits on error
$ErrorActionPreference = "Stop"

# Enable verbose output if running in CI
if ($env:CI) {
    $VerbosePreference = "Continue"
}

function usage {
    Write-Host "Usage: $(Split-Path -Leaf $MyInvocation.MyCommand.Path)"
    Write-Host "Runs linting for this project."
}

# Only run main block if the script is executed directly, not dot-sourced
if ($MyInvocation.MyCommand.Path -eq $PSCommandPath) {
    Write-Host "Running flake8..."
    & flake8 ossdbtoolsservice tests pgsmo
}