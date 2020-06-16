from ostoolsservice.scripting.contracts import ScriptOperation


SCRIPT_META_DATA: dict = {
    'Database': [ScriptOperation.CREATE, ScriptOperation.DELETE],
    'Table': [ScriptOperation.CREATE, ScriptOperation.DELETE],
    'View': [ScriptOperation.CREATE, ScriptOperation.DELETE],
    'Schema': [ScriptOperation.CREATE, ScriptOperation.DELETE],
    'Function': [ScriptOperation.CREATE, ScriptOperation.DELETE]
}
