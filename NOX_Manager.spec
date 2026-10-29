# -*- mode: python ; coding: utf-8 -*-
# Fabrication de l'exécutable : `uv run build` → dist/NOX_Manager/NOX_Manager.exe
# Onedir, fenêtré, icône et écran de démarrage (repris de 00_ancien/NOX_Manager.spec).
# Toute ressource lue à l'exécution est dans ressources/ (retrouvée par app.core.config).

a = Analysis(
    ['01_application/app/main.py'],
    pathex=['01_application'],
    binaries=[],
    datas=[('ressources', 'ressources'), ('config.json', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
splash = Splash(
    'ressources/flash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    [],
    exclude_binaries=True,
    name='NOX_Manager',
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
    icon=['ressources/LOGO_Nox.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    splash.binaries,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NOX_Manager',
)
