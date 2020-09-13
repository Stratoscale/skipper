import base64
import glob
import json
import logging
import os
import subprocess
from distutils.spawn import find_executable
from six.moves import http_client
import requests
from requests_bearer import HttpBearerAuth
import urllib3
import pkg_resources


REGISTRY_BASE_URL = 'https://%(registry)s/v2/'
IMAGE_TAGS_URL = REGISTRY_BASE_URL + '%(image)s/tags/list'
MANIFEST_URL = REGISTRY_BASE_URL + '%(image)s/manifests/%(reference)s'
DOCKER = "docker"
PODMAN = "podman"

logger = None   # pylint: disable=invalid-name

CONTAINER_RUNTIME_COMMAND = os.getenv("CONTAINER_RUNTIME_COMMAND")


def configure_logging(name, level):
    global logger   # pylint: disable=global-statement,invalid-name
    logger = logging.getLogger(name)

    formatter = logging.Formatter('[%(name)s] %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(console_handler)


def get_images_from_dockerfiles():
    dockerfiles = glob.glob(image_to_dockerfile('*'))
    images = {dockerfile_to_image(dockerfile): dockerfile for dockerfile in dockerfiles}
    return images


def local_image_exist(image, tag):
    name = image + ':' + tag
    command = [
        'images',
        '--format', '{{.ID}}',
        name
    ]
    output = run_container_command(command)
    return output != ''


def remote_image_exist(registry, image, tag, username, password):
    urllib3.disable_warnings()
    url = IMAGE_TAGS_URL % dict(registry=registry, image=image)
    headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
    response = requests.get(url=url, verify=False, headers=headers, auth=HttpBearerAuth(username, password))

    if response.status_code != http_client.OK:
        return False

    info = response.json()
    return tag in info['tags']


def get_local_images_info(images):
    command = [
        'images',
        '--format', '{"name": "{{.Repository}}", "tag": "{{.Tag}}"}',
    ]
    images_info = []
    for image in images:
        output = run_container_command(command + [image])
        if output == '':
            continue
        image_info = [json.loads(record) for record in output.splitlines()]
        images_info += [['none', info['name'], info['tag']] for info in image_info]

    return images_info


def get_remote_images_info(images, registry, username, password):
    images_info = []
    for image in images:
        images_info += get_remote_image_info(image, registry, username, password)
    return images_info


def get_remote_image_info(image, registry, username, password):
    urllib3.disable_warnings()
    image_info = []
    url = IMAGE_TAGS_URL % dict(registry=registry, image=image)
    response = requests.get(url=url, verify=False, auth=HttpBearerAuth(username, password))
    info = response.json()
    if response.ok:
        if info['tags']:
            image_info += [[registry, image, tag] for tag in info['tags']]
    else:
        if info['errors'][0]['code'] in ['NAME_UNKNOWN', 'NOT_FOUND']:
            pass
        else:
            raise Exception(info)

    return image_info


def get_image_digest(registry, image, tag, username, password):
    urllib3.disable_warnings()
    url = MANIFEST_URL % dict(registry=registry, image=image, reference=tag)
    headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
    response = requests.get(url=url, headers=headers, verify=False, auth=HttpBearerAuth(username, password))
    return response.headers['Docker-Content-Digest']


def delete_image_from_registry(registry, image, tag, username, password):
    digest = get_image_digest(registry, image, tag, username, password)
    url = MANIFEST_URL % dict(registry=registry, image=image, reference=digest)
    response = requests.delete(url=url, verify=False, auth=HttpBearerAuth(username, password))
    if not response.ok:
        raise Exception(response.content)


def delete_local_image(image, tag):
    name = image + ':' + tag
    run_container_command(['rmi', name])


def generate_fqdn_image(registry, namespace, image, tag='latest'):
    fqdn_image = image
    if namespace is not None:
        fqdn_image = namespace + '/' + fqdn_image
    if registry is not None:
        fqdn_image = registry + '/' + fqdn_image
    if tag is not None:
        fqdn_image = fqdn_image + ':' + tag
    return fqdn_image


def image_to_dockerfile(image):
    return 'Dockerfile.' + image


def dockerfile_to_image(dockerfile):
    return dockerfile.replace('Dockerfile.', '')


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    return find_executable(name) is not None


def get_runtime_command():
    global CONTAINER_RUNTIME_COMMAND  # pylint: disable=global-statement
    if not CONTAINER_RUNTIME_COMMAND:
        if is_tool(DOCKER):
            CONTAINER_RUNTIME_COMMAND = DOCKER
        elif is_tool(PODMAN):
            CONTAINER_RUNTIME_COMMAND = PODMAN
        else:
            raise Exception("Nor %s nor %s are installed" % (PODMAN, DOCKER))
    return CONTAINER_RUNTIME_COMMAND


def get_extra_file(filename):
    return pkg_resources.resource_filename("skipper", "data/%s" % filename)


def run_container_command(args):
    cmd = [get_runtime_command()]
    cmd.extend(args)
    return str(subprocess.check_output(cmd).decode().strip())


def create_path_and_add_data(full_path, data, is_file):
    directory = os.path.dirname(full_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    if is_file:
        with open(full_path, "w") as _file:
            _file.write(data)


def set_remote_registry_login_info(registry, ctx_object):
    try:
        docker_config = json.load(open('/'.join([os.path.expanduser('~'), '.docker/config.json'])))
        auth = docker_config.get('auths', {}).get(registry, {}).get('auth')
        if auth:
            username, password = base64.b64decode(auth).decode().split(r':')
            ctx_object['username'] = username
            ctx_object['password'] = password
    except Exception:  # pylint: disable=broad-except
        #  Ignore failure and just continue
        pass
