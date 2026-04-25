@echo off
setlocal
REM Launches the Native Messaging host. Chrome's manifest must point to this .cmd (or python.exe with script path per Chrome docs).
set "HERE=%~dp0"
cd /d "%HERE%"
if exist "%HERE%claude_native_host.py" (
  py -3 "%HERE%claude_native_host.py" 2>> "%HERE%host_stderr.log"
) else if exist "%HERE%..\.venv\Scripts\python.exe" (
  "%HERE%..\.venv\Scripts\python.exe" "%HERE%claude_native_host.py" 2>> "%HERE%host_stderr.log"
) else (
  python "%HERE%claude_native_host.py" 2>> "%HERE%host_stderr.log"
)
