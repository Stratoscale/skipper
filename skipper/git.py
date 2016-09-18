import subprocess


def get_hash(short=False):
    git_command = ['git', 'rev-parse']
    if short:
        git_command += ['--short']
    git_command += ['HEAD']
    return subprocess.check_output(git_command).strip()


def is_dirty():
    git_command = ['git', 'status', '--porcelain']
    dirty_files = subprocess.check_output(git_command).splitlines()
    return len(dirty_files) > 0
