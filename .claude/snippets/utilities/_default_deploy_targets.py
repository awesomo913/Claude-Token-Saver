# From: build_exe.py:13
# Deploy the --onedir build into the workspace-standard My Apps folder.

def _default_deploy_targets() -> list[Path]:
    """Deploy the --onedir build into the workspace-standard My Apps folder.

    Per ~/.claude/rules/common/exe-packaging.md, Windows builds go to
    ``~/Desktop/My Apps/<AppName>/`` (folder for --onedir) and the user
    launches via ``~/Desktop/<AppName>.lnk`` shortcut into that folder.
    """
    return [Path.home() / "Desktop" / "My Apps" / APP_NAME]
