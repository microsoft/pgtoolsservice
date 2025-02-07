# ossdbtoolsservice_main.spec
from PyInstaller.utils.hooks import collect_data_files, collect_all
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


hiddenimports = ["psycopg", "engineio.async_drivers.gevent", "xmlrpc.server"]
binaries = []
datas = []

# Include psycopg dependencies
datas += collect_data_files("psycopg")

# Collect all dependencies for debugpy
datas_debugpy, binaries_debugpy, hiddenimports_debugpy = collect_all("debugpy")
hiddenimports.extend(hiddenimports_debugpy)
datas.extend(datas_debugpy)
binaries.extend(binaries_debugpy)


# Include ossdbtoolsservice data files
def gather_service_data_files():
    # Include ossdbtoolsservice data files, but filter pg_exes dynamically
    all_datas = collect_data_files("ossdbtoolsservice", include_py_files=False)

    # Determine the current OS
    system = platform.system()
    
    def filter_pg_exes(files, system) -> list:
        """Remove non-relevant pg_exes directories based on the OS."""
        exclude_dirs = []

        if system == "Windows":
            exclude_dirs = ["pg_exes/mac", "pg_exes/linux"]
        elif system == "Darwin":
            exclude_dirs = ["pg_exes/win", "pg_exes/linux"]            
        elif system == "Linux":
            exclude_dirs = ["pg_exes/win", "pg_exes/mac"]

        filtered_files = []
        for src, dest in files:
            if not any(exclude in src.replace("\\", "/") for exclude in exclude_dirs):
                filtered_files.append((src, dest))

        return filtered_files

    # Apply the filtering
    return filter_pg_exes(all_datas, system)


datas += gather_service_data_files()

datas += [
    (
        "./ossdbtoolsservice/language/completion/packages/pgliterals/pgliterals.json",
        "language/completion/packages/pgliterals",
    )
]
datas += collect_files(
    "./ossdbtoolsservice/chat/prompts", "ossdbtoolsservice/chat/prompts", ".md"
)

# Include sql and macros files under pgsmo/objects
src_folder = "./pgsmo/objects"
dest_folder = "./pgsmo/objects"
sql_files = collect_files(src_folder, dest_folder, ".sql")
macro_files = collect_files(src_folder, dest_folder, ".macros")
datas += sql_files
datas += macro_files

# Include zlib library
if platform.system() == "Darwin" and platform.machine() == "arm64":
    if os.path.exists("/usr/local/opt/zlib/lib/libz.dylib"):
        binaries = [
            ("/usr/local/opt/zlib/lib/libz.dylib", "zlib"),
        ]

a = Analysis(
    ["ossdbtoolsservice/ossdbtoolsservice_main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ossdbtoolsservice_main",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
