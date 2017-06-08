from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages=[], excludes=[])

base = 'Console'

executables = [
    Executable('pgsqltoolsservice/pgtoolsservice_main.py', base=base)
]

setup(name='PostgreSQL Tools Service',
      version='0.1.0',
      description='Carbon data protocol server implementation for PostgreSQL',
      options=dict(build_exe=buildOptions),
      executables=executables)
