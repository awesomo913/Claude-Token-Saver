@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0open_github_app_installer.ps1"
if errorlevel 1 pause
