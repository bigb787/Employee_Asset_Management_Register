# Windows: avoids "cannot access the file ... terraform-provider-aws ... used by another process"
# by storing plugins outside the project (Defender/OneDrive/indexers often lock .terraform).
#
# Always use this wrapper for init/plan/apply in the same project:
#   .\tf.ps1 init
#   .\tf.ps1 plan
#   .\tf.ps1 apply
#
# Optional: set TERRAFORM_EXE to your binary, e.g.
#   $env:TERRAFORM_EXE = 'd:\terraformj\terraform.exe'

$ErrorActionPreference = "Stop"

$cacheRoot = Join-Path $env:USERPROFILE ".terraform-cache"
$cacheDir  = Join-Path $cacheRoot "Employee_Asset_Register"
New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
$env:TF_DATA_DIR = $cacheDir

$tfExe = $env:TERRAFORM_EXE
if (-not $tfExe) { $tfExe = "d:\terraformj\terraform.exe" }
if (-not (Test-Path -LiteralPath $tfExe)) { $tfExe = "terraform" }

Push-Location $PSScriptRoot
try {
  & $tfExe @args
  exit $LASTEXITCODE
} finally {
  Pop-Location
}
