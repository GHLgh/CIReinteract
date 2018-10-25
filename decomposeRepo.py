from GitReplay import GitReplay
from SetupManager import ExperimentHelper

MAX_ROLLOUT = 5
EXAMPLE_DIR = "/Users/ghlgh/Desktop/Courework.nosync/CS 599DM/gluo-joda-time"

if __name__ == "__main__":
    git_repo = GitReplay(EXAMPLE_DIR)
    # clean up
    git_repo.delete_all_branches_with_tag()
    git_repo.delete_all_branches_with_tag("ekstazi")
    
    # building branches
    git_repo.build_seeds_from_recent_commits(EXAMPLE_DIR, MAX_ROLLOUT)
    git_repo.create_experiment_branches_with_tag("ekstazi", git_repo.get_existing_seed(), ExperimentHelper.get_setup_function("ekstazi", "travis"))
    
    # increment commit history only when the build for the experiment branches are done
    # otherwise, no RTS artifact can be utilized (run in parallel)
    # however, it won't matter if you limit the number of concurrent jobs on travis
    # git_repo.proceed_commit_history("ekstazi")
    exit(0)
