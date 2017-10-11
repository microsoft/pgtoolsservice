from prompt_toolkit.completion import Completion    # noqa


class ExtendCompletion(Completion):
    """
    This class extends prompt_toolkit.completion class to include specific fields (eg. schema)
    while sending completions based on token text in pgcompleter.
    """

    def __init__(self, text, start_position=0, display=None, display_meta=None,
                 get_display_meta=None, schema=None):
        self.schema = schema
        super(ExtendCompletion, self).__init__(text, start_position, display, display_meta,
                                               get_display_meta)
