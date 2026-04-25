#Requires -Version 5.1
<#
.SYNOPSIS
  Launch the PyInstaller build of Claude Token Saver (ClaudeTokenSaver.exe).
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Exe = Join-Path $Root "dist\ClaudeTokenSaver\ClaudeTokenSaver.exe"
$DesktopCopy = Join-Path ([Environment]::GetFolderPath("Desktop")) "ClaudeTokenSaver\ClaudeTokenSaver.exe"

if (-not (Test-Path -LiteralPath $Exe)) {
    if (Test-Path -LiteralPath $DesktopCopy) {
        $Exe = $DesktopCopy
    } else {
        Write-Host "Built exe not found. Tried:" -ForegroundColor Yellow
        Write-Host "  $(Join-Path $Root "dist\ClaudeTokenSaver\ClaudeTokenSaver.exe")" -ForegroundColor DarkGray
        Write-Host "  $DesktopCopy" -ForegroundColor DarkGray
        $build = Join-Path $Root "build_exe.py"
        Write-Host "Build with:  py -3 `"$build`"" -ForegroundColor Cyan
        Write-Host "Or from source:  py -3 -m claude_backend.gui" -ForegroundColor Cyan
        exit 1
    }
}

Write-Host "Starting: $Exe"
Start-Process -FilePath $Exe
exit 0
