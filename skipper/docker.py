import logging
import os
import subprocess


def _run_command(cmd):
    logging.debug(" ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    output = []
    while proc.poll() is None:
        line = proc.stdout.readline()
        output.append(line.rstrip())
        logging.debug(line.rstrip())

    return output


def build(path, dockerfile, tag='latest'):
    docker_cmd = [
        "docker",
        "build",
        "-f", dockerfile,
        "-t", tag,
        path
    ]

    _run_command(docker_cmd)


def run(workspace, project, uid, gid, fqdn_image, command):
    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--net", "host",
        "-v", "%(workspace)s:/workspace:rw,Z" % dict(workspace=workspace),
        "-v", "/var/lib/osmosis:/var/lib/osmosis:rw,Z" % dict(workspace=workspace),
        "-v", "/var/run/docker.sock:/var/run/docker.sock:Z",
        "-u", "%(uid)d:%(gid)d" % dict(uid=uid, gid=gid),
        "-w", "%(workdir)s" % dict(workdir=os.path.join("/workspace", project)),
        "--entrypoint", command[0],
        fqdn_image
    ]

    return _run_command(docker_cmd + command[1:])
