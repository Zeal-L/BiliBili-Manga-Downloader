# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import subprocess

version = "1.5.1"

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/assets/easy-taskbar-progress.dll', 'src/assets'),
        ('src/ui/PySide_src/imgs', 'src/ui/PySide_src/imgs'),
        ('src/ui/PySide_src/mainWindow.ui', 'src/ui/PySide_src'),
        ('src/ui/PySide_src/myAbout.ui', 'src/ui/PySide_src'),
        ('src/ui/PySide_src/qrCode.ui', 'src/ui/PySide_src'),
        ('src/ui/PySide_src/resource.qrc', 'src/ui/PySide_src'),
    ],
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
    name='BiliBili Manga Downloader',
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
    name='BiliBili Manga Downloader',
)
app = BUNDLE(
    coll,
    name='BiliBili Manga Downloader.app',
    icon='src/ui/PySide_src/imgs/icon.icns',
    bundle_identifier=None,
    info_plist={
            'CFBundleDisplayName': 'BiliBili Manga Downloader',
            'CFBundleName': 'BiliBili Manga Downloader',
            'CFBundlePackageType': 'APPL',
            'CFBundleSignature': 'BMDL',
            'CFBundleShortVersionString': version,
            'CFBundleVersion': version,
            'CFBundleExecutable': 'BiliBili Manga Downloader',
            'CFBundleIconFile': 'icon.icns',
            'CFBundleIdentifier': 'dev.zeal.bmdler',
            'CFBundleInfoDictionaryVersion': '6.0',
            'LSApplicationCategoryType': 'public.app-category.graphics-design',
            'LSEnvironment': {'LANG': 'zh_CN.UTF-8'},
            }
)
