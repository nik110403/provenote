<#
.SYNOPSIS
  Install the external tools the provenote helpers need (Windows).
.DESCRIPTION
  winget first, choco fallback. -Workflow pdf|build|all, -Typst, -DryRun, -Yes.
  Ends by running doctor and exiting with its code. Exit 3: no package manager.
#>
param(
    [ValidateSet('pdf', 'build', 'all')][string]$Workflow = 'all',
    [switch]$Typst,
    [switch]$DryRun,
    [switch]$Yes
)
$ErrorActionPreference = 'Stop'
$doctor = Join-Path $PSScriptRoot '..\plugins\provenote\bin\doctor'

# tool -> winget id / choco id (mirrors plugins/provenote/bin/doctor)
$catalog = @{
    pdftotext = @{ winget = 'oschwartz10612.Poppler'; choco = 'poppler' }
    pandoc    = @{ winget = 'JohnMacFarlane.Pandoc'; choco = 'pandoc' }
    typst     = @{ winget = 'Typst.Typst'; choco = 'typst' }
}
$want = @()
if ($Workflow -in 'pdf', 'all') { $want += 'pdftotext' }
if ($Workflow -in 'build', 'all') { $want += 'pandoc' }
if ($Typst) { $want += 'typst' }

$missing = @()
foreach ($tool in $want) {
    if (Get-Command $tool -CommandType Application -ErrorAction SilentlyContinue) { Write-Host "skip: $tool already installed" }
    else { $missing += $tool }
}

$manager = $null
if (Get-Command winget -CommandType Application -ErrorAction SilentlyContinue) { $manager = 'winget' }
elseif (Get-Command choco -CommandType Application -ErrorAction SilentlyContinue) { $manager = 'choco' }
if (-not $manager -and $missing.Count -gt 0) {
    [Console]::Error.WriteLine('install-deps: no package manager found (neither winget nor choco). Install App Installer (winget) or https://chocolatey.org/install, or install poppler and pandoc manually.')
    exit 3
}

# each command: @{ exe = ...; args = @(...) } so nothing goes through Invoke-Expression
$cmds = @()
foreach ($tool in $missing) {
    if ($manager -eq 'winget') { $cmds += @{ exe = 'winget'; args = @('install', '--id', $catalog[$tool].winget, '-e', '--source', 'winget', '--accept-source-agreements', '--accept-package-agreements') } }
    else { $cmds += @{ exe = 'choco'; args = @('install', '-y', $catalog[$tool].choco) } }
}
if ($cmds.Count -eq 0) { Write-Host 'Nothing to install.' }
else {
    Write-Host 'Commands to run:'
    $cmds | ForEach-Object { Write-Host "  $($_.exe) $($_.args -join ' ')" }
}
if ($DryRun) { exit 0 }

if ($cmds.Count -gt 0) {
    if (-not $Yes) {
        $answer = Read-Host 'Run these commands? [y/N]'
        if ($answer -notmatch '^(y|yes)$') { Write-Host 'Aborted.'; exit 1 }
    }
    foreach ($c in $cmds) {
        $exe = $c.exe; $cargs = $c.args
        & $exe @cargs
        # winget: 0x8A15002B no applicable upgrade, 0x8A150061 already installed -> success
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189 -and $LASTEXITCODE -ne -1978335135) {
            [Console]::Error.WriteLine("install-deps: failed: $exe $($cargs -join ' ')"); exit 1
        }
    }
    Write-Host 'Open a new terminal if a freshly installed tool is not found on PATH.'
}

if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 $doctor --workflow $Workflow }
else { & python $doctor --workflow $Workflow }
exit $LASTEXITCODE
