import os.path
import logging
import subprocess


def get_hash(short=False):
    if not os.path.exists('.git'):
        logging.warning('*** Not working in a git repository ***')
        return 'none'

    git_command = ['git', 'rev-parse']
    if short:
        git_command += ['--short']
    git_command += ['HEAD']

    if uncommitted_changes():
        logging.warning("*** Uncommitted changes present - Build container version might be outdated ***")

    return subprocess.check_output(git_command).strip().decode('utf-8')


def uncommitted_changes():
    """Return True is there are uncommitted changes."""
    return subprocess.call(['git', 'diff', '--quiet', 'HEAD']) != 0
