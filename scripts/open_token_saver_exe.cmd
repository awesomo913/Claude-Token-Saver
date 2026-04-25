@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0open_token_saver_exe.ps1"
if errorlevel 1 pause
