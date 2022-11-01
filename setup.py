from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(
    build_exe = "build/mysqltoolsservice",
    packages = ['asyncio', 'jinja2', 'pymysql', 'inflection', 'sqlparse', 'prompt_toolkit', 'xlsxwriter', 'nose2', 'parameterized', 'coverage', 'autopep8', 'flake8', 'debugpy', '_pydev_runfiles', 'pythonnet'],
    excludes = [],
    include_files = [],
    replace_paths = [("*", "")]
)

base = 'Console'

executables = [
    Executable('ossdbtoolsservice/ossdbtoolsservice_main.py', base=base)
]

setup(
    name = 'OSS Databases Tools Service',
    version = '1.6.2',
    description = 'Carbon data protocol server implementation for PostgreSQL',
    options = dict(build_exe=buildOptions),
    executables = executables
)
