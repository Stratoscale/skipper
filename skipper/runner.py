import grp
import getpass
import logging
import os
import subprocess
from contextlib import contextmanager


def run(command, fqdn_image=None, environment=None, interactive=False, name=None, net='host', volumes=None, workdir=None):
    if fqdn_image is not None:
        return _run_nested(fqdn_image, environment, command, interactive, name, net, volumes, workdir)

    return _run(command)


def _run(cmd):
    logger = logging.getLogger('skipper')
    logger.debug(' '.join(cmd))
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc.returncode


# pylint: disable=too-many-locals
def _run_nested(fqdn_image, environment, command, interactive, name, net='host', volumes=None, workdir=None):
    cwd = os.getcwd()
    workspace = os.path.dirname(cwd)
    project = os.path.basename(cwd)

    docker_cmd = ['docker', 'run']
    if interactive:
        docker_cmd += ['-i']
    if name:
        docker_cmd += ['--name', name]

    docker_cmd += ['-t']
    docker_cmd += ['--rm']
    docker_cmd += ['--privileged']

    docker_cmd += ['--net', net]

    environment = environment or []
    for env in environment:
        docker_cmd += ['-e', env]

    user = getpass.getuser()
    user_id = os.getuid()
    docker_cmd += ['-e', 'SKIPPER_USERNAME=%(user)s' % dict(user=user)]
    docker_cmd += ['-e', 'SKIPPER_UID=%(user_id)s' % dict(user_id=user_id)]

    docker_gid = grp.getgrnam('docker').gr_gid
    docker_cmd += ['-e', 'SKIPPER_DOCKER_GID=%(docker_gid)s' % dict(docker_gid=docker_gid)]

    volumes = volumes or []

    volumes.extend([
        '%(workspace)s:%(workspace)s:rw,Z' % dict(workspace=workspace),
        '/var/lib/osmosis:/var/lib/osmosis:rw,Z' % dict(workspace=workspace),
        '/var/run/docker.sock:/var/run/docker.sock:Z',
        '/opt/skipper/skipper-entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:Z',
    ])
    for volume in volumes:
        docker_cmd += ['-v', volume]

    if workdir:
        docker_cmd += ['-w', workdir]
    else:
        docker_cmd += ['-w', '%(workdir)s' % dict(workdir=os.path.join(workspace, project))]

    docker_cmd += ['--entrypoint', '/opt/skipper/skipper-entrypoint.sh']
    docker_cmd += [fqdn_image]
    docker_cmd += [' '.join(command)]

    with _network(net):
        ret = _run(docker_cmd)

    return ret


@contextmanager
def _network(net):
    if _network_exists(net):
        yield
    else:
        _create_network(net)
        yield
        _destroy_network(net)


def _create_network(net):
    logging.debug("Creating network %(net)s", dict(net=net))
    subprocess.check_output(['docker', 'network', 'create', net])


def _destroy_network(net):
    logging.debug("Deleting network %(net)s", dict(net=net))
    subprocess.check_output(['docker', 'network', 'rm', net])


def _network_exists(net):
    result = subprocess.check_output(['docker', 'network', 'ls', '-q', '-f', 'NAME=%s' % net])
    return len(result) > 0
