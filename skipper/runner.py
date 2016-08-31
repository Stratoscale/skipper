import grp
import logging
import os
import subprocess


def run(command, fqdn_image=None, environment=None):
    if fqdn_image is not None:
        cwd = os.getcwd()
        workspace = os.path.dirname(cwd)
        project = os.path.basename(cwd)

        uid = os.getuid()
        gid = grp.getgrnam('docker').gr_gid
        _run_nested(workspace, project, uid, gid, fqdn_image, environment, command)
    else:
        _run(command)


def _run(cmd):
    logging.debug(" ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    output = []
    while True:
        line = proc.stdout.readline()
        if line == '' and proc.poll() is not None:
            break
        output.append(line.rstrip())
        logging.debug(line.rstrip())

    return output


def _run_nested(workspace, project, uid, gid, fqdn_image, environment, command):
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

    return _run(docker_cmd + command[1:])
