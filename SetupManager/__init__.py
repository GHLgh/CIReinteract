from functools import partial
from .setupFunctions import ekstazi_setup

class ExperimentHelper:
    def __init__(self):
        pass

    @staticmethod
    def get_setup_function(tag, ci_tool, override_run_command = False):
        return {
            "ekstazi": partial(ekstazi_setup, ci_tool, override_run_command)
        }.get(tag.lower(), None)