from GitReplay import GitReplay
from SetupManager import ExperimentHelper
import os

MAX_ROLLOUT = 5
EXAMPLE_DIR = os.path.join(os.environ.get('REPO_BASE'),"gluo-joda-time")

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

    # here using skip_ci as workaround, in this case, the CI will not run the "incremented" content
    # until a notification is received from CI, the notification indicates that the build for "pre-incremented" content
    # has been completed (RTS artifacts generated).
    # The notification is a way to inform us the experiment can move on.
    # Now the notification is sent to a pre-defined Azure function
    # [TODO generalize it such that user can define where to send the notification]
    # git_repo.proceed_commit_history("ekstazi", skip_ci=True)

    # A hack to be able to trigger "incremented" build later on
    # Create an empty commit on tool_seed branch such that later Git merge will success and trigger CI build with notification.
    # git_repo.generate_empty_commit_on_experiment_seeds("ekstazi")

    exit(0)
