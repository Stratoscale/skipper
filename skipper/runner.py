import getpass
import grp
import logging
import os
import subprocess
from contextlib import contextmanager
import sys
from retry import retry
from skipper import utils


# pylint: disable=too-many-arguments
def run(command, fqdn_image=None, environment=None, interactive=False, name=None, net='host', volumes=None,
        workdir=None, use_cache=False, workspace=None):
    if fqdn_image is not None:
        return _run_nested(fqdn_image, environment, command, interactive, name, net, volumes,
                           workdir, use_cache, workspace)

    return _run(command)


def _run(cmd_args):
    logger = logging.getLogger('skipper')
    cmd = [utils.get_runtime_command()]
    cmd.extend(cmd_args)
    logger.debug(' '.join(cmd))
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc.returncode


# pylint: disable=too-many-locals
# pylint: disable=too-many-arguments
def _run_nested(fqdn_image, environment, command, interactive, name, net, volumes, workdir, use_cache, workspace):
    cwd = os.getcwd()
    if workspace is None:
        workspace = os.path.dirname(cwd)
    homedir = os.path.expanduser('~')
    cmd = ['run']
    if interactive:
        cmd += ['-i']
    if name:
        cmd += ['--name', name]

    cmd += ['-t']

    if os.environ.get("KEEP_CONTAINERS", False):
        cmd += ['-e', 'KEEP_CONTAINERS=True']
    else:
        cmd += ['--rm']

    cmd += ['--privileged']

    cmd += ['--net', net]

    environment = environment or []
    for env in environment:
        cmd += ['-e', env]

    user = getpass.getuser()
    user_id = os.getuid()
    cmd += ['-e', 'SKIPPER_USERNAME=%(user)s' % dict(user=user)]
    cmd += ['-e', 'SKIPPER_UID=%(user_id)s' % dict(user_id=user_id)]
    cmd += ['-e', 'HOME=%(homedir)s' % dict(homedir=homedir)]

    if utils.get_runtime_command() == "docker":
        docker_gid = grp.getgrnam('docker').gr_gid
        cmd += ['-e', 'SKIPPER_DOCKER_GID=%(docker_gid)s' % dict(docker_gid=docker_gid)]

    if use_cache:
        cmd += ['-e', 'SKIPPER_USE_CACHE_IMAGE=True']

    cmd = handle_volumes_bind_mount(cmd, homedir, volumes, workspace)

    if workdir:
        cmd += ['-w', workdir]
    else:
        cmd += ['-w', '%(workdir)s' % dict(workdir=cwd)]

    cmd += ['--entrypoint', '/opt/skipper/skipper-entrypoint.sh']
    cmd += [fqdn_image]
    cmd += [' '.join(command)]

    with _network(net):
        ret = _run(cmd)

    return ret


def handle_volumes_bind_mount(docker_cmd, homedir, volumes, workspace):
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

        # For OSX, map anything in /var/lib or /etc to /private
        if sys.platform == 'darwin':
            if volume.startswith('/etc/') or volume.startswith('/var/lib/'):
                volume = '/private' + volume

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
    return docker_cmd


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
    utils.run_container_command(['network', 'create', net])


@retry(delay=0.1, tries=10)
def _destroy_network(net):
    logging.debug("Deleting network %(net)s", dict(net=net))
    utils.run_container_command(['network', 'rm', net])


def _network_exists(net):
    cmd = ['network', 'ls']
    if utils.get_runtime_command() == "docker":
        cmd.extend(["-f", "NAME=%s" % net])
    else:
        cmd.append("-q")
    result = utils.run_container_command(cmd)
    return net in result
