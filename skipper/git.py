import subprocess


def get_hash(short=False):
    git_command = ['git', 'rev-parse']
    if short:
        git_command += ['--short']
    git_command += ['HEAD']
    return subprocess.check_output(git_command).strip()
