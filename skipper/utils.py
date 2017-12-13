import glob
import json
import logging
import subprocess
from six.moves import http_client
import requests
import urllib3


REGISTRY_BASE_URL = 'https://%(registry)s/v2/'
IMAGE_TAGS_URL = REGISTRY_BASE_URL + '%(image)s/tags/list'
MANIFEST_URL = REGISTRY_BASE_URL + '%(image)s/manifests/%(reference)s'

logger = None   # pylint: disable=invalid-name


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
        'docker',
        'images',
        '--format', '{{.ID}}',
        name
    ]
    output = subprocess.check_output(command).decode()
    return output != ''


def remote_image_exist(registry, image, tag):
    urllib3.disable_warnings()
    url = IMAGE_TAGS_URL % dict(registry=registry, image=image)
    response = requests.get(url=url, verify=False)

    if response.status_code != http_client.OK:
        return False

    info = response.json()
    return tag in info['tags']


def get_local_images_info(images):
    command = [
        'docker',
        'images',
        '--format', '{"name": "{{.Repository}}", "tag": "{{.Tag}}"}',
    ]
    images_info = []
    for image in images:
        output = subprocess.check_output(command + [image]).decode()
        if output == '':
            continue
        image_info = [json.loads(record) for record in output.splitlines()]
        images_info += [['none', info['name'], info['tag']] for info in image_info]

    return images_info


def get_remote_images_info(images, registry):
    images_info = []
    for image in images:
        images_info += get_remote_image_info(image, registry)
    return images_info


def get_remote_image_info(image, registry):
    urllib3.disable_warnings()
    image_info = []
    url = IMAGE_TAGS_URL % dict(registry=registry, image=image)
    response = requests.get(url=url, verify=False)
    info = response.json()
    if response.ok:
        image_info += [[registry, image, tag] for tag in info['tags']]
    else:
        if info['errors'][0]['code'] == 'NAME_UNKNOWN':
            pass
        else:
            raise Exception(info)

    return image_info


def get_image_digest(registry, image, tag):
    urllib3.disable_warnings()
    url = MANIFEST_URL % dict(registry=registry, image=image, reference=tag)
    headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
    response = requests.get(url=url, headers=headers, verify=False)
    return response.headers['Docker-Content-Digest']


def delete_image_from_registry(registry, image, tag):
    digest = get_image_digest(registry, image, tag)
    url = MANIFEST_URL % dict(registry=registry, image=image, reference=digest)
    response = requests.delete(url=url, verify=False)
    if not response.ok:
        raise Exception(response.content)


def delete_local_image(image, tag):
    name = image + ':' + tag
    subprocess.check_call(['docker', 'rmi', name])


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
