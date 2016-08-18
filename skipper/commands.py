import grp
import logging
import os
import pwd
import re
import yaml
from skipper import docker
from skipper import git


USER = os.environ["USER"]
GROUP = "docker"


def build(registry, image, dockerfile, tag=None):
    workspace = os.getcwd()
    tag = tag or git.get_hash(True)
    fqdn_image = _generate_fqdn_image(registry, image, tag)
    docker.build(workspace, dockerfile, fqdn_image)


def run(registry, image, tag, command):
    fqdn_image = _generate_fqdn_image(registry, image, tag)

    cwd = os.getcwd()
    workspace = os.path.dirname(cwd)
    project = os.path.basename(cwd)

    uid = pwd.getpwnam(USER).pw_uid
    gid = grp.getgrnam(GROUP).gr_gid

    if len(command) == 0:
        logging.error('Command was not provided')
    else:
        return docker.run(workspace, project, uid, gid, fqdn_image, command)


def make(registry, image, tag, makefile, target):
    command = ['make', '-f', makefile, target]
    run(registry, image, tag, command)


def depscheck(registry, image, tag, manifesto_path):
    installed_pips = _get_installed_pips(registry, image, tag)
    official_pips = _get_official_pips(manifesto_path)
    _compare_pips(installed_pips, official_pips)


def _generate_fqdn_image(registry, image, tag='latest'):
    return registry + '/' + image + ':' + tag


def _get_installed_pips(registry, image, tag):
    command = ['pip', 'freeze', '--disable-pip-version-check']
    output = run(registry, image, tag, command)
    installed_pips = {}
    for line in output:
        if len(line) > 0:
            pip, version = re.match(r'([^=]+)===?([^=]+)', line).groups()
        installed_pips[pip] = version

    return installed_pips


def _get_official_pips(manifesto_path):
    with open(manifesto_path) as manifesto_file:
        manifesto = yaml.load(manifesto_file)

    official_pips = {}
    for req in manifesto['requirements']:
        if req.get('pips') is not None:
            official_pips.update({pip_name: req.get('revision') for pip_name in req.get('pips')})

    return official_pips


def _compare_pips(installed_pips, official_pips):
    for installed_pip, installed_version in installed_pips.iteritems():
        official_version = official_pips.get(installed_pip)
        # TODO: remove this check once we support version check of non-strato packages
        if official_version is None:
            continue
        if installed_version != official_version:
            logging.error('Version mismatch for package %(pip)s: %(installed_version)s != %(official_version)s',
                          dict(pip=installed_pip, installed_version=installed_version, official_version=official_version))
