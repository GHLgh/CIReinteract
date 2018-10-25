from functools import partial
from .setupFunctions import ekstazi_setup

class ExperimentHelper:
    def __init__(self):
        pass

    @staticmethod
    def get_setup_function(tag, ci_tool):
        return {
            "ekstazi": partial(ekstazi_setup, ci_tool)
        }.get(tag.lower(), None)