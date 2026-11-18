# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop_standalone.pyw'],
    pathex=[],
    binaries=[],
    datas=[('D:/erea/db.sqlite3', '.'), ('D:/erea/backup', 'backup'), ('D:/erea/masha/templates/masha', 'masha/templates/masha')],
    hiddenimports=[],
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
    name='desktop_standalone',
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
    name='desktop_standalone',
)
