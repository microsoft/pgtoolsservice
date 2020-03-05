from cx_Freeze import setup, Executable
import os

# Dependencies are automatically detected, but it might need
# fine tuning.
include_files = [('./pgsqltoolsservice/pg_exes', './pg_exes')]
buildOptions = dict(packages=['asyncio'], excludes=[], include_files=include_files)

base = 'Console'

executables = [
    Executable('pgsqltoolsservice/pgtoolsservice_main.py', base=base)
]

os.environ['TCL_LIBRARY'] = r'C:\Users\swjain\AppData\Local\Programs\Python\Python36-32\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\swjain\AppData\Local\Programs\Python\Python36-32\tcl\tk8.6'

setup(name='PostgreSQL Tools Service',
      version='0.1.0',
      description='Carbon data protocol server implementation for PostgreSQL',
      options=dict(build_exe=buildOptions),
      executables=executables)
