import grp
import getpass
import logging
import os
import subprocess


def run(command, fqdn_image=None, environment=None, interactive=False):
    if fqdn_image is not None:
        return _run_nested(fqdn_image, environment, command, interactive)
    else:
        return _run(command)


def _run(cmd):
    logger = logging.getLogger('skipper')
    logger.debug(' '.join(cmd))
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc.returncode


def _run_nested(fqdn_image, environment, command, interactive):
    cwd = os.getcwd()
    workspace = os.path.dirname(cwd)
    project = os.path.basename(cwd)

    docker_cmd = ['docker', 'run']
    if interactive:
        docker_cmd += ['-i']

    docker_cmd += ['-t']
    docker_cmd += ['--rm']
    docker_cmd += ['--net', 'host']

    environment = environment or []
    for env in environment:
        docker_cmd += ['-e', env]

    user = getpass.getuser()
    user_id = os.getuid()
    docker_cmd += ['-e', 'SKIPPER_USERNAME=%(user)s' % dict(user=user)]
    docker_cmd += ['-e', 'SKIPPER_UID=%(user_id)s' % dict(user_id=user_id)]

    docker_gid = grp.getgrnam('docker').gr_gid
    docker_cmd += ['-e', 'SKIPPER_DOCKER_GID=%(docker_gid)s' % dict(docker_gid=docker_gid)]

    volumes = [
        '%(workspace)s:%(workspace)s:rw,Z' % dict(workspace=workspace),
        '/var/lib/osmosis:/var/lib/osmosis:rw,Z' % dict(workspace=workspace),
        '/var/run/docker.sock:/var/run/docker.sock:Z',
        '/opt/skipper/skipper-entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:Z',
    ]
    for volume in volumes:
        docker_cmd += ['-v', volume]

    docker_cmd += ['-w', '%(workdir)s' % dict(workdir=os.path.join(workspace, project))]
    docker_cmd += ['--entrypoint', '/opt/skipper/skipper-entrypoint.sh']
    docker_cmd += [fqdn_image]
    docker_cmd += [' '.join(command)]

    return _run(docker_cmd)
