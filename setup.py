from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
include_files = [('./ossdbtoolsservice/pg_exes', './pg_exes')]
buildOptions = dict(packages=['asyncio', 'jinja2', 'psycopg2', 'pymysql', 'inflection', 'sqlparse',
                              'prompt_toolkit', 'xlsxwriter', 'nose', 'parameterized', 'coverage', 'autopep8', 'flake8', 'debugpy', '_pydev_runfiles'],
                    excludes=[], include_files=include_files)

base = 'Console'

executables = [
    Executable('ossdbtoolsservice/ossdbtoolsservice_main.py', base=base)
]

setup(name='OSS Databases Tools Service',
      version='1.6.0',
      description='Carbon data protocol server implementation for PostgreSQL',
      options=dict(build_exe=buildOptions),
      executables=executables)
