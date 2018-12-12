from GitReplay import GitReplay
from GitReplay import populate_GitReplays
from SetupManager import ExperimentHelper
import os

MAX_ROLLOUT = 5

# The directory that contain all the git projects you want to evaluate the RTS tools on
REPO_BASE = os.environ.get('REPO_BASE')
RTS_TOOLS = ["ekstazi"]

if __name__ == "__main__":
    git_repos = populate_GitReplays(REPO_BASE)
    # [TODO] for testing only
    # git_repos = [GitReplay("/Users/ghlgh/Desktop/Courework.nosync/CS 599DM/repos/gluo-joda-time")]

    for git_repo in git_repos:
        # clean up such that this script can run repeatly for manual testing
        # delete all branches with "seed" in the branch name
        git_repo.delete_all_branches_with_tag()
        for tool_tag in RTS_TOOLS:
            git_repo.delete_all_branches_with_tag(tool_tag)
        
        # building branches
        git_repo.build_seeds_from_recent_commits(MAX_ROLLOUT)
        for tool_tag in RTS_TOOLS:
            git_repo.create_experiment_branches_with_tag( \
                tool_tag, git_repo.get_existing_seed(), \
                ExperimentHelper.get_setup_function(tool_tag, "travis", True))
        
        # Note that if you are using Travis-CI (presumably also other CI tools),
        # increment commit history only when the initial build for the experiment branches are done
        # otherwise, no RTS artifact can be utilized (different builds on the same branch are run in parallel)
        # however, it won't matter if you limit the number of concurrent jobs on CI

        # Right now, this tool rely on Azure function to perform the increment step.
        # Azure function is served as a reflector to receive the notification from initial build and trigger the increment step

    exit(0)
