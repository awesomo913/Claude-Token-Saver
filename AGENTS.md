# Agent notes — GitHub App Installer

- **Name:** The application is **GitHub App Installer**. Do not refer to it as “Claude Token Saver” in user-facing strings (historical GitHub repo name may still be Claude-Token-Saver).
- **Windows exe:** `dist/GitHubAppInstaller/GitHubAppInstaller.exe`. After `build_exe.py`, a full copy is deployed to `Desktop/GitHubAppInstaller/`.
- **Launch script:** `scripts/open_github_app_installer.ps1` (tries `dist\` first, then Desktop copy).
- **PyInstaller entry:** `launch_github_app_installer.py`. Spec: `GitHubAppInstaller.spec`.
