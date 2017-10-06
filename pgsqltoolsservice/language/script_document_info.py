import sqlparse

from pgsqltoolsservice.workspace.contracts import Position, TextDocumentPosition
from pgsqltoolsservice.workspace.script_file import ScriptFile
from pgsqltoolsservice.language.text import TextUtilities
from pgsqltoolsservice.language.script_parse_info import ScriptParseInfo


class ScriptDocumentInfo:
    def __init__(self, text_document_position: TextDocumentPosition, script_file: ScriptFile, script_parse_info: ScriptParseInfo=None):
        self.start_line = text_document_position.position.line
        self.parser_line = text_document_position.position.line + 1
        self.start_column = TextUtilities.prev_delimiter_pos(text_document_position.position.line, text_document_position.position.character)
        self.end_column = TextUtilities.next_delimiter_pos(text_document_position.position.line, text_document_position.position.character)
        self.parser_column = text_document_position.position.character + 1
        self.contents = script_file.file_lines
        self.script_parse_info = script_parse_info

    @classmethod
    def from_script_parse_info(cls, text_document_position: TextDocumentPosition, script_file: ScriptFile, script_parse_info: ScriptParseInfo):
        #todo: validate script_parse_info not none
        return cls(text_document_position, script_file, script_parse_info)

    # @classmethod
    # def get_token(cls, script_parse_info: ScriptParseInfo, start_line: int, start_column: int):
    #     if script_parse_info is not None:# and sqlparse.parse(script_parse_info.document.text):
    #         pass
            
    @classmethod
    def get_peek_definition_tokens(cls, script_parse_info: ScriptParseInfo, start_line: int, start_coloumn: int):
        pass
