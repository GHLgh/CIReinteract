import re
import os
from subprocess import call, check_output, STDOUT

class GitReplay:
    def __init__(self, repo_dir):
        self.repo_dir_ = repo_dir
        if not self.is_git_dir():
            self.repo_dir_ = None

    def is_git_dir(self):
        return (call(["git", "branch"], stderr=STDOUT, stdout=open(os.devnull, 'w'), cwd=self.repo_dir_) == 0)

    def build_seeds_from_recent_commits(self, num_rollout, push=True):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return False
        for i in range(5):
            call(['git', 'checkout', 'master~{}'.format(i)], cwd=self.repo_dir_)
            call(['git', 'checkout', '-b', 'seed_{}'.format(i)], cwd=self.repo_dir_)
        print("Done generating seeds")
        if push:
            call(['git', 'push', '--all'], cwd=self.repo_dir_)
            print("Done pushing seeds")
        return True

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

    def get_existing_seed(self):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return []
        # check_output returns byte string
        byteRes = check_output(["git", "for-each-ref", r"--format='%(refname:short)'", r"refs/heads/seed*"], cwd=self.repo_dir_)
        seed_index_pattern = re.compile(r'seed_(\d+)')
        return [int(x) for x in seed_index_pattern.findall(byteRes.decode("utf-8"))]

    def get_experiment_branches_with_tag(self, tag):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return []
        # check_output returns byte string
        byteRes = check_output(["git", "for-each-ref", r"--format='%(refname:short)'", r"refs/heads/{}*".format(tag)], cwd=self.repo_dir_)
        seed_index_pattern = re.compile(r'{}_(\d+)-\d+'.format(tag))
        return [int(x) for x in seed_index_pattern.findall(byteRes.decode("utf-8"))]

    def create_experiment_branches_with_tag(self, tag, seed_index_list, experiment_setup_function=None, push=True):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return False
        for idx in seed_index_list:
            call(['git', 'checkout', 'seed_{}'.format(idx)], cwd=self.repo_dir_)
            call(['git', 'checkout', '-b', '{}_seed_{}'.format(tag, idx)], cwd=self.repo_dir_)
            self._perform_setup(tag, experiment_setup_function)
            # idx 0 is the seed of the most recent commit
            if idx != 0:
                call(['git', 'checkout', '-b', '{}_{}-{}'.format(tag, idx, idx-1)], cwd=self.repo_dir_)
        print("Done generating experiment branches")
        if push:
            call(['git', 'push', '--all'], cwd=self.repo_dir_)
            print("Done pushing experiment branches")
        return True

    def _perform_setup(self, tag, experiment_setup_function):
        if experiment_setup_function is not None:
            modified_files = experiment_setup_function(self.repo_dir_)
            for modified_file in modified_files:
                call(['git', 'add', '{}'.format(modified_file)], cwd=self.repo_dir_)
            if len(modified_files) > 0:
                call(['git', 'commit', '-m', 'Modified for {}'.format(tag)], cwd=self.repo_dir_)

    def proceed_commit_history(self, tag, push=True):
        if self.repo_dir_ is None:
            print("Not a Git directory")
            return False
        idx_list = self.get_experiment_branches_with_tag(tag)
        for idx in idx_list:
            next_commit_idx = idx - 1
            call(['git', 'checkout', '{}_{}-{}'.format(tag, idx, next_commit_idx)], cwd=self.repo_dir_)
            call(['git', 'merge', '--strategy-option=theirs', '-m "increment commit to recent {}"'.format(next_commit_idx), '{}_seed_{}'.format(tag, next_commit_idx)], cwd=self.repo_dir_)
        print("Done proceeding experiment branches")
        if push:
            call(['git', 'push', '--all'], cwd=self.repo_dir_)
            print("Done pushing experiment branches")