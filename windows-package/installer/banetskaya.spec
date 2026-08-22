# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the Banetskaya.by desktop build.
# Run from the repository root on Windows:  pyinstaller windows-package/installer/banetskaya.spec --noconfirm
import os
from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
BACKEND = os.path.join(ROOT, "backend")
ICON = os.path.join(SPECPATH, "assets", "icon.ico")

datas = [
    (os.path.join(BACKEND, "templates"), "templates"),
    (os.path.join(BACKEND, "assets"), "assets"),
    (os.path.join(ROOT, "frontend", "build"), "frontend_build"),
]
# Bundled portable MongoDB (downloaded by the CI workflow into resources/mongodb)
_mongo = os.path.join(ROOT, "resources", "mongodb")
if os.path.isdir(_mongo):
    datas.append((_mongo, "mongodb"))

hiddenimports = [
    "server", "document_service", "_buildinfo",
    "motor", "motor.motor_asyncio", "pymongo", "bson", "dns",
    "uvicorn", "uvicorn.logging",
    "uvicorn.loops", "uvicorn.loops.auto",
    "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan", "uvicorn.lifespan.on",
    "docxtpl", "docx", "openpyxl", "jinja2", "pypdf",
    "lxml", "lxml._elementpath", "email_validator",
    "requests", "pymupdf",
]

binaries = []

block_cipher = None

a = Analysis(
    [os.path.join(BACKEND, "desktop_main.py")],
    pathex=[BACKEND],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Banetskaya",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=ICON,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Banetskaya",
)
