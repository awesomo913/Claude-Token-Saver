#Requires -Version 5.1
<#
.SYNOPSIS
  Launch the PyInstaller-built Claude Token Saver (ClaudeTokenSaver.exe).
.NOTES
  Repo root is the parent of this scripts/ folder. Agents: run this when the user
  wants the standalone exe; if missing, build with: py -3 build_exe.py
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Exe = Join-Path $Root "dist\ClaudeTokenSaver\ClaudeTokenSaver.exe"

if (-not (Test-Path -LiteralPath $Exe)) {
    Write-Host "Built exe not found: $Exe" -ForegroundColor Yellow
    $build = Join-Path $Root "build_exe.py"
    Write-Host "Build with:  py -3 `"$build`"" -ForegroundColor Cyan
    Write-Host "Or from source:  py -3 -m claude_backend.gui" -ForegroundColor Cyan
    exit 1
}

Write-Host "Starting: $Exe"
Start-Process -FilePath $Exe
exit 0
