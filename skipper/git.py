import logging
import os
import subprocess


def get_hash(short=False):
    if not is_git_repository():
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


def is_git_repository():
    if os.path.exists('.git'):
        return True
    command = ['git', 'rev-parse', '--is-inside-work-tree']
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
