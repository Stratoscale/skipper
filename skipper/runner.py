import getpass
import grp
import logging
import os
import subprocess
from contextlib import contextmanager
import sys
from retry import retry
from skipper import utils


def get_default_net():
    # The host networking driver only works on Linux hosts, and is not supported on Docker Desktop for Mac,
    # Docker Desktop for Windows, or Docker EE for Windows Server.
    return 'host' if sys.platform != 'darwin' and sys.platform != 'win32' else 'bridge'


# pylint: disable=too-many-arguments
def run(command, fqdn_image=None, environment=None, interactive=False, name=None, net=None, publish=(), volumes=None,
        workdir=None, use_cache=False, workspace=None, env_file=()):

    if not net:
        net = get_default_net()

    if fqdn_image is not None:
        return _run_nested(fqdn_image, environment, command, interactive, name, net, publish, volumes,
                           workdir, use_cache, workspace, env_file)

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
def _run_nested(fqdn_image, environment, command, interactive, name, net, publish, volumes, workdir, use_cache, workspace, env_file):
    cwd = os.getcwd()
    if workspace is None:
        workspace = os.path.dirname(cwd)
    homedir = os.path.expanduser('~')
    cmd = ['run']
    if interactive:
        cmd += ['-i']
        cmd += ['-e', 'SKIPPER_INTERACTIVE=True']
    if name:
        cmd += ['--name', name]

    cmd += ['-t']

    if os.environ.get("KEEP_CONTAINERS", False):
        cmd += ['-e', 'KEEP_CONTAINERS=True']
    else:
        cmd += ['--rm']

    cmd += ['--privileged']

    cmd = handle_networking(cmd, publish, net)

    for _file in env_file:
        cmd += ['--env-file', _file]

    environment = environment or []
    for env in environment:
        cmd += ['-e', env]

    user = getpass.getuser()
    user_id = os.getuid()
    cmd += ['-e', 'SKIPPER_USERNAME=%(user)s' % dict(user=user)]
    cmd += ['-e', 'SKIPPER_UID=%(user_id)s' % dict(user_id=user_id)]
    cmd += ['-e', 'HOME=%(homedir)s' % dict(homedir=homedir)]

    if utils.get_runtime_command() == "docker":
        try:
            docker_gid = grp.getgrnam('docker').gr_gid
            cmd += ['-e', 'SKIPPER_DOCKER_GID=%(docker_gid)s' % dict(docker_gid=docker_gid)]
        except KeyError:
            pass

    if use_cache:
        cmd += ['-e', 'SKIPPER_USE_CACHE_IMAGE=True']

    cmd = handle_volumes_bind_mount(cmd, homedir, volumes, workspace)

    cmd = handle_workdir(cmd, cwd, workdir)

    cmd += ['--entrypoint', '/opt/skipper/skipper-entrypoint.sh']
    cmd += [fqdn_image]
    cmd += [' '.join(command)]

    with _network(net):
        ret = _run(cmd)

    return ret


def handle_workdir(cmd, cwd, workdir):
    if workdir:
        cmd += ['-w', workdir]
    else:
        cmd += ['-w', '%(workdir)s' % dict(workdir=cwd)]
    return cmd


def handle_networking(cmd, publish, net):
    if publish:
        for port_mapping in publish:
            cmd += ['-p', port_mapping]

    if net is not None:
        cmd += ['--net', net]

    return cmd


def handle_volumes_bind_mount(docker_cmd, homedir, volumes, workspace):
    volumes = volumes or []
    volumes.extend(['%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=homedir),
                    '%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=homedir),
                    '%(homedir)s/.docker/config.json:%(homedir)s/.docker/config.json:ro' % dict(homedir=homedir)])

    # required for docker login (certificates)
    if os.path.exists('/etc/docker'):
        volumes.append('/etc/docker:/etc/docker:ro')

    if utils.get_runtime_command() == utils.PODMAN:
        volumes.extend([
            '%(workspace)s:%(workspace)s:rw,shared' % dict(workspace=workspace),
            '%s:/opt/skipper/skipper-entrypoint.sh:rw' % utils.get_extra_file("skipper-entrypoint.sh"),
        ])
        if os.path.exists('/var/run/docker.sock'):
            volumes.append('/var/run/docker.sock:/var/run/docker.sock:rw')
        if os.path.exists('/var/lib/osmosis'):
            volumes.append('/var/lib/osmosis:/var/lib/osmosis:rw')
    else:
        volumes.extend([
            '%(workspace)s:%(workspace)s:rw' % dict(workspace=workspace),
            '/var/run/docker.sock:/var/run/docker.sock:rw',
            '%s:/opt/skipper/skipper-entrypoint.sh' % utils.get_extra_file("skipper-entrypoint.sh"),
            ])
        # Will fail on Mac
        if os.path.exists('/var/lib/osmosis'):
            volumes.append('/var/lib/osmosis:/var/lib/osmosis:rw')

    for volume in volumes:
        if ":" not in volume:
            raise ValueError("Volume entry is badly-formatted - %s" % volume)

        # For OSX, map anything in /var/lib or /etc to /private
        if sys.platform == 'darwin':
            if volume.startswith('/etc/') or volume.startswith('/var/lib/'):
                volume = '/private' + volume

        # if part of host directory is empty, skipping this mount
        if not volume.split(":")[0]:
            continue

        create_vol_localpath_if_needed(volume)
        docker_cmd += ['-v', volume]

    return docker_cmd


def create_vol_localpath_if_needed(volume):
    host_path = volume.split(":")[0].strip()
    # We have couple of special case mounts
    # 1. gitconfig file - it is required by skipper but may not exists, we don't want
    # to create folder if it doesn't exist
    # that's why we create it as file
    # 2. .docker/config.json - if it is required and doesn't exists we want to create is as file with {} as data
    if ".gitconfig" in host_path and not os.path.exists(host_path):
        utils.create_path_and_add_data(full_path=host_path, data="", is_file=True)
    elif "docker/config.json" in host_path and not os.path.exists(host_path):
        utils.create_path_and_add_data(full_path=host_path, data="{}", is_file=True)
    elif not os.path.exists(host_path):
        # If the local directory of a mount entry doesn't exist, docker will by
        # default create a directory in that path. Docker runs in systemd context,
        # with root-privileges, so the container will have no permissions to write
        # to that directory. To prevent that, we'll create the directory in advance,
        # with the user's permissions
        try:
            os.makedirs(host_path)
        except OSError:
            # If we have no permissions to create the directory, we'll just let
            # docker create it with root-privileges
            pass


@contextmanager
def _network(net):
    if utils.get_runtime_command() != "docker":
        yield
    elif _network_exists(net):
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
    cmd = ['network', 'ls', "-f", "NAME=%s" % net]
    result = utils.run_container_command(cmd)
    return net in result
