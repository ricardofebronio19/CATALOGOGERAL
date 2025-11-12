                # -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import sys
import os

# Coletar dados
datas = [('templates', 'templates'), ('static', 'static'), ('version.json', '.')]

# Coletar binários - incluindo extensões asyncio do Windows
binaries = []

# Adicionar _overlapped.pyd explicitamente
python_dir = os.path.dirname(sys.executable)
dll_dir = os.path.join(python_dir, 'DLLs')
overlapped_path = os.path.join(dll_dir, '_overlapped.pyd')
if os.path.exists(overlapped_path):
    binaries.append((overlapped_path, '.'))
    
# Adicionar _asyncio.pyd se existir
asyncio_path = os.path.join(dll_dir, '_asyncio.pyd')
if os.path.exists(asyncio_path):
    binaries.append((asyncio_path, '.'))

# Hiddenimports essenciais
hiddenimports = [
    'app',
    'models',
    'routes',
    'core_utils',
    'utils.image_utils',
    'utils.import_utils',
    'waitress',
    'flask',
    'flask_sqlalchemy',
    'flask_login',
    'asyncio',
    '_overlapped',
    '_asyncio',
    '_winapi',
    'sqlalchemy.ext.baked',
    'webbrowser',
]


a = Analysis(
    ['run.py'],  # VERSÃO NAVEGADOR
    pathex=[os.getcwd()],
    binaries=binaries,
    datas=datas,
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
    a.binaries,
    a.datas,
    [],
    name='CatalogoDePecas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['static\\favicon.ico'],
)
