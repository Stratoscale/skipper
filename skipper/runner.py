import grp
import getpass
import logging
import os
import subprocess


def run(command, fqdn_image=None, environment=None, interactive=False, net='host', volumes=None, workdir=None):
    if fqdn_image is not None:
        return _run_nested(fqdn_image, environment, command, interactive, net, volumes, workdir)
    else:
        return _run(command)


def _run(cmd):
    logger = logging.getLogger('skipper')
    logger.debug(' '.join(cmd))
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc.returncode


# pylint: disable=too-many-locals
def _run_nested(fqdn_image, environment, command, interactive, net='host', volumes=None, workdir=None):
    _create_network(net)
    cwd = os.getcwd()
    workspace = os.path.dirname(cwd)
    project = os.path.basename(cwd)

    docker_cmd = ['docker', 'run']
    if interactive:
        docker_cmd += ['-i']

    docker_cmd += ['-t']
    docker_cmd += ['--rm']

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

    return _run(docker_cmd)


def _create_network(net):
    if not _network_exists(net):
        logging.debug("Network %(net)s does not exist. Creating...", dict(net=net))
        subprocess.check_output(['docker', 'network', 'create', net])


def _network_exists(net):
    result = subprocess.check_output(['docker', 'network', 'ls', '-q', '-f', 'NAME=%s' % net])
    return len(result) > 0
