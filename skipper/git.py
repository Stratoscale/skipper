import logging
import subprocess


def get_hash(short=False):
    git_command = ['git', 'rev-parse']
    if short:
        git_command += ['--short']
    git_command += ['HEAD']

    if uncommitted_changes():
        logging.warning("*** Uncommitted changes present - Build container version might be outdated ***")

    return subprocess.check_output(git_command).strip()


def uncommitted_changes():
    """Return True is there are uncommitted changes."""
    return subprocess.call(['git', 'diff-index', '--quiet', 'HEAD', '--']) != 0
