#Requires -Version 5.1
<#
.SYNOPSIS
  Launch the PyInstaller build of GitHub App Installer (GitHubAppInstaller.exe).
.NOTES
  Dist folder: dist\GitHubAppInstaller\ — also copied to %USERPROFILE%\Desktop\GitHubAppInstaller
  when you run build_exe.py. Build: py -3 build_exe.py
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Exe = Join-Path $Root "dist\GitHubAppInstaller\GitHubAppInstaller.exe"
$DesktopCopy = Join-Path ([Environment]::GetFolderPath("Desktop")) "GitHubAppInstaller\GitHubAppInstaller.exe"

if (-not (Test-Path -LiteralPath $Exe)) {
    if (Test-Path -LiteralPath $DesktopCopy) {
        $Exe = $DesktopCopy
    } else {
        Write-Host "Built exe not found. Tried:" -ForegroundColor Yellow
        Write-Host "  $($(Join-Path $Root "dist\GitHubAppInstaller\GitHubAppInstaller.exe"))" -ForegroundColor DarkGray
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
