from functools import partial
from .setupFunctions import *

class ExperimentHelper:
    def __init__(self):
        pass

    @staticmethod
    def get_setup_function(tag, ci_tool, override_run_command = False, upload_reports = False):
        rts_setup_function = {
            "ekstazi" : partial(ekstazi_setup),
            "starts" : partial(starts_setup),
        }.get(tag.lower(), None)

        ci_setup_function = {
            "travis" : partial(travis_setup, tag.lower(), override_run_command, upload_reports)
        }.get(ci_tool.lower(), None)

        return partial(setup_template, rts_setup_function, ci_setup_function)