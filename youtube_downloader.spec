# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[('app.py', '.'), ('requirements.txt', '.'), ('templates', 'templates')],
    hiddenimports=['flask', 'werkzeug', 'jinja2', 'markupsafe', 'click', 'itsdangerous'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='YouTubeDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=None,  # Add icon.icns here if you have one
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
