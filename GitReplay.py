import re
import os
from subprocess import call, check_output, STDOUT

# GitReplay class is a wrapper of the pipeline purposed in README to simplify the interaction
# with git and CI
class GitReplay:
    # Constructor that instantiate the GitReplay object with respect to the provided directory
    # @param repo_dir: the path to directory that is a git directory
    def __init__(self, repo_dir):
        self.repo_dir_ = repo_dir
        if not self.is_git_dir():
            self.repo_dir_ = None

    # Check if the GitReplay object is referring to a git directory
    # @return True if it is a git directory, False otherwise
    def is_git_dir(self):
        return (call(["git", "branch"], stderr=STDOUT, stdout=open(os.devnull, 'w'), cwd=self.repo_dir_) == 0)

    # Create additional branches that reflect individual commits
    # It will generate the following branches:
    #   * seed_{idx} where {idx} represents that the content of this branch
    #       is equivalent to the commit {idx} away from current HEAD
    # For instance, if there are two commits (commit_0, commit_1) to be rolled out,
    # it will result in two additional branches seed_0, seed_1
    # where the content of seed_0 is identical to commit_0 and seed_1 is identical to commit_1
    # @param num_rollout: the maximum number of commits to be rolled out [TODO] check return value
    # @param push: boolean to indicate if the created branches will be pushed to remote
    # return True if the creation is success, False otherwise.
    def build_seeds_from_recent_commits(self, num_rollout, push=True):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return False
        for i in range(num_rollout):
            call(['git', 'checkout', 'master~{}'.format(i)], cwd=self.repo_dir_)
            call(['git', 'checkout', '-b', 'seed_{}'.format(i)], cwd=self.repo_dir_)
        print("Done generating seeds")
        if push:
            call(['git', 'push', '--all'], cwd=self.repo_dir_)
            print("Done pushing seeds")
        return True

    # Delete the branches that contain "tag" in their names
    # NOTE: Given that it only check the "tag" in name, please make sure
    #   that the original branches in the repository doesn't contain "seed"
    #   and other string used as tag in their names
    # @param tag: the string used to filter the branches to be deleted
    # return True if the deletion is success, False otherwise.
    def delete_all_branches_with_tag(self, tag="seed"):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return False
        # make sure no seeds are checked out
        call(['git', 'checkout', 'master'], cwd=self.repo_dir_)
        call(["git push origin --delete $(git for-each-ref --format='%(refname:short)' refs/heads/{}*)".format(tag)], cwd=self.repo_dir_, shell=True)
        call(["git branch -D $(git for-each-ref --format='%(refname:short)' refs/heads/{}*)".format(tag)], cwd=self.repo_dir_, shell=True)
        print("Done deleting seeds")
        return True

    # Obtain a list of seed index in the repository
    # NOTE: Given that it only check substring "seed_{idx}" in name, please make sure
    #   that the original branches in the repository don't have name in this format
    # return a list of the seed index in integer
    def get_existing_seed(self):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return []
        # check_output returns byte string
        byteRes = check_output(["git", "for-each-ref", r"--format='%(refname:short)'", r"refs/heads/seed*"], cwd=self.repo_dir_)
        seed_index_pattern = re.compile(r'seed_(\d+)')
        return [int(x) for x in seed_index_pattern.findall(byteRes.decode("utf-8"))]

    # Obtain a list of index of seed with "tag" in the repository
    # NOTE: Given that it only check substring "{tag}_seed_{idx}" in name, please make sure
    #   that the original branches in the repository don't have name in this format
    # @param tag: the string used to filter the branches to be selected
    # return a list of the seed index in integer
    def get_experiment_seed_with_tag(self, tag):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return []
        # check_output returns byte string
        byteRes = check_output(["git", "for-each-ref", r"--format='%(refname:short)'", r"refs/heads/{}_seed*".format(tag)], cwd=self.repo_dir_)
        seed_index_pattern = re.compile(r'.*seed_(\d+)')
        return [int(x) for x in seed_index_pattern.findall(byteRes.decode("utf-8"))]

    # Obtain a list of index of experiment branches with "tag" in the repository
    # NOTE: Given that it only check substring "{tag}_{idx}-{idx-1}" in name, please make sure
    #   that the original branches in the repository don't have name in this format
    # @param tag: the string used to filter the branches to be selected
    # return a list of the index in integer
    def get_experiment_branches_with_tag(self, tag):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return []
        # check_output returns byte string
        byteRes = check_output(["git", "for-each-ref", r"--format='%(refname:short)'", r"refs/heads/{}*".format(tag)], cwd=self.repo_dir_)
        seed_index_pattern = re.compile(r'{}_(\d+)-\d+'.format(tag))
        return [int(x) for x in seed_index_pattern.findall(byteRes.decode("utf-8"))]

    # Create the experiment branches for generating RTS results later on
    # The following branches will be generated:
    #   * {tag}_seed_{idx} where the content is equivalent to seed_{idx} with
    #       modification by experiment_setup_function
    #   * {tag}_{idx}-{idx-1} where the content is equivalent to {tag}_seed_{idx},
    #       those branches will be used to generate RTS results later on
    # @param tag: the tag used for identifying the generated branches
    # @param seed_index_list: the list of index to create the experiment branches from,
    #    note that the index should be valid (the seed_{idx} branch exists)
    # @param experiment_setup_function: the function to be called to set up the experiment branches,
    #    for instance, setting up the RTS tool as Maven plugin and modifying the Travis configuration
    # @param push: boolean to indicate if the created branches will be pushed to remote
    # return True if the creation is success, False otherwise.
    def create_experiment_branches_with_tag(self, tag, seed_index_list, experiment_setup_function=None, push=True):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return False
        # using merely max idx to start the creation assumes that no seeds are missing
        call(['git', 'checkout', 'seed_{}'.format(max(seed_index_list))], cwd=self.repo_dir_)
        # propagate the rest
        for idx in reversed(range(max(seed_index_list)+1)):
            call(['git', 'checkout', '-b', '{}_seed_{}'.format(tag, idx)], cwd=self.repo_dir_)
            call(['git', 'merge', '--strategy-option=theirs', \
                '-m', "Recent {} commit".format(idx), 'seed_{}'.format(idx)], cwd=self.repo_dir_)
            #call(['git', 'checkout', 'seed_{}'.format(idx)], cwd=self.repo_dir_)
            self._perform_setup(tag, experiment_setup_function)
            # idx 0 is the seed of the most recent commit
            if idx != 0:
                call(['git', 'checkout', '-b', '{}_{}-{}'.format(tag, idx, idx-1)], cwd=self.repo_dir_)
                #self._generate_empty_commit('{}_{}-{}'.format(tag, idx, idx-1))
        print("Done generating experiment branches")
        if push:
            call(['git', 'push', '--all'], cwd=self.repo_dir_)
            print("Done pushing experiment branches")
        return True

    # The helper function to call the experiment_setup_function
    # and commit the changes via git
    # @param tag: tag to identify the commit
    # @param experiment_setup_function: the function to be called to set up the experiment branches
    # @param skip_ci: boolean to specify if this commit will trigger CI,
    #    note that it only works for Travis CI for now because the skip string is hard-coded
    #    to what Travis CI can recognize
    def _perform_setup(self, tag, experiment_setup_function, skip_ci=False):
        skip_ci_string = ""
        if skip_ci:
            skip_ci_string = "[skip ci]"
        if experiment_setup_function is not None:
            modified_files = experiment_setup_function(self.repo_dir_)
            for modified_file in modified_files:
                call(['git', 'add', '{}'.format(modified_file)], cwd=self.repo_dir_)
            if len(modified_files) > 0:
                call(['git', 'commit', '-m', '{}Modified for {}'.format(skip_ci_string, tag)], cwd=self.repo_dir_)

    # Update the content of experiment branches by one commit, for instance,
    # if the experiment branch is {tag}_{idx}-{idx-1}, it will be merged with
    # seed_{idx-1} such that it simulates the behavior of programmer makes 
    # new changes and commits it
    # Note that this function is not being used because the same procedure
    # is done by Azure function
    # @param tag: tag to identify the commit
    # @param push: boolean to indicate if the created branches will be pushed to remote
    # @param skip_ci: boolean to specify if this commit will trigger CI,
    #    note that it only works for Travis CI for now because the skip string is hard-coded
    #    to what Travis CI can recognize
    def proceed_commit_history(self, tag, push=True, skip_ci=False):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return False
        skip_ci_string = ""
        if skip_ci:
            skip_ci_string = "[skip ci]"
        idx_list = self.get_experiment_branches_with_tag(tag)
        for idx in idx_list:
            next_commit_idx = idx - 1
            call(['git', 'checkout', '{}_{}-{}'.format(tag, idx, next_commit_idx)], cwd=self.repo_dir_)
            call(['git', 'merge', '--strategy-option=theirs', \
                '-m', "{}increment commit to recent {}".format(skip_ci_string, next_commit_idx), '{}_seed_{}'.format(tag, next_commit_idx)], \
                cwd=self.repo_dir_)
        print("Done proceeding experiment branches")
        if push:
            call(['git', 'push', '--all'], cwd=self.repo_dir_)
            print("Done pushing experiment branches")

    # It creates new empty commits on the experiment seeds such that
    # the experiment seeds will be different from any existing branches for sure.
    # Note that it is also not being used as it is used in previous procedure
    # @param tag: tag to identify the commit
    # @param push: boolean to indicate if the created branches will be pushed to remote
    def generate_empty_commit_on_experiment_seeds(self, tag, push=True):
        idx_list = self.get_experiment_seed_with_tag(tag)
        for idx in idx_list:
            self._generate_empty_commit('{}_seed_{}'.format(tag, idx))
        print("Done generating empy commit for branches with tag {}".format(tag))
        if push:
            call(['git', 'push', '--all'], cwd=self.repo_dir_)
            print("Done pushing experiment branches")

    # Helper function to create empty commit on specific branch
    # @param branch: the branch to create empty commit on
    def _generate_empty_commit(self, branch):
        call(['git', 'checkout', '{}'.format(branch)], cwd=self.repo_dir_)
        call(['git', 'commit', '--allow-empty', '-m "Empty commit to allow meaningless merge"'], cwd=self.repo_dir_)

# Function that instantiate the git directories as GitReplay objects
# @param repo_base: the path of the directory that contains git directories as sub-directories (non-recurssive)
# @return list of valid GitReplay objects
def populate_GitReplays(repo_base):
    res = []
    sub_directories = [os.path.join(repo_base, o) for o in os.listdir(repo_base) if os.path.isdir(os.path.join(repo_base,o))]
    for directory in sub_directories:
        replay_instance = GitReplay(directory)
        if replay_instance.is_git_dir():
            res.append(replay_instance)
    return res
