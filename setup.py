from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
include_files = [('./ostoolsservice/pg_exes', './pg_exes')]
buildOptions = dict(packages=['asyncio', 'jinja2', 'psycopg2', 'pymysql', 'inflection', 'sqlparse',
'prompt_toolkit', 'xlsxwriter', 'nose', 'parameterized', 'coverage', 'autopep8', 'flake8'], 
excludes=["tkinter"], include_files=include_files)

base = 'Console'

executables = [
    Executable('ostoolsservice/ostoolsservice_main.py', base=base)
]

setup(name='PostgreSQL Tools Service',
      version='0.1.0',
      description='Carbon data protocol server implementation for PostgreSQL',
      options=dict(build_exe=buildOptions),
      executables=executables)
