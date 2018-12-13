import os
from optparse import OptionParser

from GitReplay import GitReplay
from GitReplay import populate_GitReplays
from SetupManager import ExperimentHelper

MAX_ROLLOUT = 5

# The directory that contain all the git projects you want to evaluate the RTS tools on
REPO_BASE = os.environ.get('REPO_BASE')

RTS_TOOLS = ["ekstazi", "starts"]

if __name__ == "__main__":
    usage = "usage: python %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--clean", action="store_true", dest="clean",
                    help="clean branches related to the experiment first if any")
    (options, args) = parser.parse_args()
    
    git_repos = populate_GitReplays(REPO_BASE)

    for git_repo in git_repos:
        # clean up such that this script can run repeatly for manual testing
        # delete all branches with "seed" in the branch name
        if options.clean is not None:
            git_repo.delete_all_branches_with_tag()
            for tool_tag in RTS_TOOLS:
                git_repo.delete_all_branches_with_tag(tool_tag)
        
        # building branches
        git_repo.build_seeds_from_recent_commits(MAX_ROLLOUT)
        for tool_tag in RTS_TOOLS:
            git_repo.create_experiment_branches_with_tag( \
                tool_tag, git_repo.get_existing_seed(), \
                ExperimentHelper.get_setup_function(tool_tag, "travis", True, True))
        
        # Note that if you are using Travis-CI (presumably also other CI tools),
        # increment commit history only when the initial build for the experiment branches are done
        # otherwise, no RTS artifact can be utilized (different builds on the same branch are run in parallel)
        # however, it won't matter if you limit the number of concurrent jobs on CI

        # Right now, this tool rely on Azure function to perform the increment step.
        # Azure function is served as a reflector to receive the notification from initial build and trigger the increment step

    exit(0)
