# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['claude_backend', 'claude_backend.gui', 'claude_backend.backend', 'claude_backend.config', 'claude_backend.types', 'claude_backend.storage', 'claude_backend.manifest', 'claude_backend.search', 'claude_backend.prompt_builder', 'claude_backend.tracker', 'claude_backend.ollama_manager', 'claude_backend.scanners', 'claude_backend.scanners.project', 'claude_backend.scanners.local', 'claude_backend.scanners.github', 'claude_backend.analyzers', 'claude_backend.analyzers.code_extractor', 'claude_backend.analyzers.pattern_detector', 'claude_backend.analyzers.structure_mapper', 'claude_backend.generators', 'claude_backend.generators.claude_md', 'claude_backend.generators.memory_files', 'claude_backend.generators.snippet_library']
hiddenimports += collect_submodules('customtkinter')


a = Analysis(
    ['claude_backend\\gui.py'],
    pathex=[],
    binaries=[],
    datas=[('claude_backend', 'claude_backend')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ClaudeTokenSaver',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClaudeTokenSaver',
)
