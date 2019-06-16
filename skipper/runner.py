import getpass
import grp
import logging
import os
import subprocess
from contextlib import contextmanager

from retry import retry


# pylint: disable=too-many-arguments
def run(command, fqdn_image=None, environment=None, interactive=False, name=None, net='host', volumes=None, workdir=None, use_cache=False):
    if fqdn_image is not None:
        return _run_nested(fqdn_image, environment, command, interactive, name, net, volumes, workdir, use_cache)

    return _run(command)


def _run(cmd):
    logger = logging.getLogger('skipper')
    logger.debug(' '.join(cmd))
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc.returncode


# pylint: disable=too-many-locals
# pylint: disable=too-many-arguments
def _run_nested(fqdn_image, environment, command, interactive, name, net, volumes, workdir, use_cache):
    cwd = os.getcwd()
    workspace = os.path.dirname(cwd)
    project = os.path.basename(cwd)
    homedir = os.path.expanduser('~')

    docker_cmd = ['docker', 'run']
    if interactive:
        docker_cmd += ['-i']
    if name:
        docker_cmd += ['--name', name]

    docker_cmd += ['-t']

    if os.environ.get("KEEP_CONTAINERS", False):
        docker_cmd += ['-e', 'KEEP_CONTAINERS=True']
    else:
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
    docker_cmd += ['-e', 'HOME=%(homedir)s' % dict(homedir=homedir)]

    docker_gid = grp.getgrnam('docker').gr_gid
    docker_cmd += ['-e', 'SKIPPER_DOCKER_GID=%(docker_gid)s' % dict(docker_gid=docker_gid)]

    if use_cache:
        docker_cmd += ['-e', 'SKIPPER_USE_CACHE_IMAGE=True']

    volumes = volumes or []

    volumes.extend([
        '%(workspace)s:%(workspace)s:rw,Z' % dict(workspace=workspace),
        '%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=homedir),
        '%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=homedir),
        '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
        '/var/run/docker.sock:/var/run/docker.sock:Z',
        '/opt/skipper/skipper-entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:Z',
    ])
    for volume in volumes:
        if ":" not in volume:
            raise ValueError("Volume entry is badly-formatted - %s" % volume)

        # If the local directory of a mount entry doesn't exist, docker will by
        # default create a directory in that path. Docker runs in systemd context,
        # with root-privileges, so the container will have no permissions to write
        # to that directory. To prevent that, we'll create the directory in advance,
        # with the user's permissions
        localdir = volume.split(":")[0]
        if not os.path.exists(localdir.strip()):
            try:
                os.makedirs(localdir)
            except OSError:
                # If we have no permissions to create the directory, we'll just let
                # docker create it with root-privileges
                pass

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
    subprocess.check_output(['docker', 'network', 'create', net]).decode()


@retry(delay=0.1)
def _destroy_network(net):
    logging.debug("Deleting network %(net)s", dict(net=net))
    subprocess.check_output(['docker', 'network', 'rm', net]).decode()


def _network_exists(net):
    result = subprocess.check_output(['docker', 'network', 'ls', '-q', '-f', 'NAME=%s' % net]).decode()
    return len(result) > 0
