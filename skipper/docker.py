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


def run(workspace, project, uid, gid, fqdn_image, environment, command):
    docker_cmd = ["docker", "run"]
    docker_cmd += ["--rm"]
    docker_cmd += ["--net", "host"]

    environment = environment or []
    for env in environment:
        docker_cmd += ["-e", env]

    volumes = [
        "%(workspace)s:/workspace:rw,Z" % dict(workspace=workspace),
        "/var/lib/osmosis:/var/lib/osmosis:rw,Z" % dict(workspace=workspace),
        "/var/run/docker.sock:/var/run/docker.sock:Z",
    ]
    for volume in volumes:
        docker_cmd += ["-v", volume]

    docker_cmd += ["-u", "%(uid)d:%(gid)d" % dict(uid=uid, gid=gid)]
    docker_cmd += ["-w", "%(workdir)s" % dict(workdir=os.path.join("/workspace", project))]
    docker_cmd += ["--entrypoint", command[0]]
    docker_cmd += [fqdn_image]

    return _run_command(docker_cmd + command[1:])
