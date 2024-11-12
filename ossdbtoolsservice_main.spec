# ossdbtoolsservice_main.spec
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_all
import psycopg
import platform
import os

block_cipher = None

def collect_files(src_folder, dest_folder, file_ext=None):
    collected_files = []
    for root, dirs, files in os.walk(src_folder):
        for file in files:
            if not file_ext or file.endswith(file_ext):
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, src_folder)
                dest_path = os.path.join(dest_folder, rel_path)
                collected_files.append((src_path, dest_path))

    return collected_files

# Include psycopg dependencies
hiddenimports = collect_submodules('psycopg')
datas = collect_data_files('psycopg')

# Collect all dependencies for debugpy
datas_debugpy, binaries_debugpy, hiddenimports_debugpy = collect_all("debugpy")

# Extend the existing hiddenimports array (or create it if it's not defined)
hiddenimports = hiddenimports if 'hiddenimports' in locals() else []
hiddenimports.extend(hiddenimports_debugpy)

# Extend the existing datas array (or create it if it's not defined)
datas = datas if 'datas' in locals() else []
datas.extend(datas_debugpy)

# Add xmlrpc.server to hiddenimports
hiddenimports.append('xmlrpc.server')

# Include ossdbtoolsservice data files
datas += collect_data_files('ossdbtoolsservice', include_py_files=False)
datas += [('./ossdbtoolsservice/language/completion/packages/pgliterals/pgliterals.json', 'language/completion/packages/pgliterals')]

# Include sql and macros files under pgsmo/objects
src_folder = './pgsmo/objects'
dest_folder = './pgsmo/objects'
sql_files = collect_files(src_folder, dest_folder, ".sql")
macro_files = collect_files(src_folder, dest_folder, ".macros")
datas += sql_files
datas += macro_files

# Include zlib library
if platform.system() == 'Darwin' and platform.machine() == 'arm64':
    binaries = [
        ('/usr/local/opt/zlib/lib/libz.dylib', 'zlib'),
    ]

# Collect all dependencies for new requirements
datas_flask, binaries_flask, hiddenimports_flask = collect_all("flask")
datas_flask_cors, binaries_flask_cors, hiddenimports_flask_cors = collect_all("flask_cors")
datas_flask_socketio, binaries_flask_socketio, hiddenimports_flask_socketio = collect_all("flask_socketio")
datas_gevent, binaries_gevent, hiddenimports_gevent = collect_all("gevent")
datas_gevent_websocket, binaries_gevent_websocket, hiddenimports_gevent_websocket = collect_all("gevent_websocket")

# Extend the existing hiddenimports array
hiddenimports.extend(hiddenimports_flask)
hiddenimports.extend(hiddenimports_flask_cors)
hiddenimports.extend(hiddenimports_flask_socketio)
hiddenimports.extend(hiddenimports_gevent)
hiddenimports.extend(hiddenimports_gevent_websocket)

# Extend the existing datas array
datas.extend(datas_flask)
datas.extend(datas_flask_cors)
datas.extend(datas_flask_socketio)
datas.extend(datas_gevent)
datas.extend(datas_gevent_websocket)

# Extend the existing binaries array if it exists
binaries = binaries if 'binaries' in locals() else []
binaries.extend(binaries_flask)
binaries.extend(binaries_flask_cors)
binaries.extend(binaries_flask_socketio)
binaries.extend(binaries_gevent)
binaries.extend(binaries_gevent_websocket)

a = Analysis(
    ['ossdbtoolsservice_main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ossdbtoolsservice_main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ossdbtoolsservice_main',
)