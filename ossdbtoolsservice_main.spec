# ossdbtoolsservice_main.spec
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import psycopg
import platform

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

# Include files and directories
include_files = [('./ossdbtoolsservice/pg_exes', './pg_exes')]

# Include psycopg dependencies
hiddenimports = collect_submodules('psycopg')
datas = collect_data_files('psycopg')

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
else:
    binaries = []

a = Analysis(['ossdbtoolsservice/ossdbtoolsservice_main.py'],
             pathex=['/Users/yimdaeun/Projects/pgtoolsservice/'],
             binaries=binaries,
             datas=datas + include_files,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='ossdbtoolsservice_main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True)
