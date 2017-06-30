from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
include_files = [
    './pgsmo/objects/column/templates', 
    './pgsmo/objects/database/templates', 
    './pgsmo/objects/role/templates', 
    './pgsmo/objects/schema/templates', 
    './pgsmo/objects/server/templates', 
    './pgsmo/objects/table/templates', 
    './pgsmo/objects/tablespace/templates', 
    './pgsmo/objects/view/view_templates'
]

buildOptions = dict(packages=['asyncio'], excludes=[], include_files=include_files)

base = 'Console'

executables = [
    Executable('pgsqltoolsservice/pgtoolsservice_main.py', base=base)
]

setup(name='PostgreSQL Tools Service',
      version='0.1.0',
      description='Carbon data protocol server implementation for PostgreSQL',
      options=dict(build_exe=buildOptions),
      executables=executables)
