# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Folder tema (QSS files)
        ('widgets/*', 'widgets'),
        # Seluruh isi modules (payloads, dll)
        ('modules/**/*', 'modules'),
        # Folder bin (console.py dll)
        ('bin/*', 'bin'),
        # Folder core (utils, dll)
        ('core/*', 'core'),
        # Jika ada banner atau file lain
        # ('banner/*', 'banner'),
        # Jika ada icon atau resource lain
        # ('icon.ico', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.sip',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtNetwork',
        'PyQt6.QtWebChannel',
        # Tambahkan jika ada modul lain yang sering hilang (misal rich, faulthandler)
        'rich',
        'faulthandler',
        'json',
        'datetime',
        'threading',
        'subprocess',
        'signal',
        'os',
        'sys',
        'io',
        're',
        'time',
        'random',
        'shutil',
        'pathlib',
        'dataclasses',
        'typing',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pkg_resources',           # ← ini penting untuk menghindari NullProvider error
        'pkg_resources.extern',
        'setuptools',
        '_pytest',                 # jika tidak dipakai
        'pytest',
        'tkinter',                 # jika pure PyQt6
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LazyFramework',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                      # kompres ukuran (butuh upx terinstal)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                  # ubah ke False jika ingin tanpa console (pure GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'                # ganti dengan path icon kamu jika ada (untuk Windows)
)

# Jika ingin folder terpisah (onedir) bukan satu file
# COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='LazyFramework')