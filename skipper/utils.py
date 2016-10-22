import glob
import json
import logging
import subprocess
import requests

REGISTRY_BASE_URL = 'https://%(registry)s/v2/'
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
    images = [dockerfile_to_image(dockerfile) for dockerfile in dockerfiles]
    return images


def local_image_exist(image, tag):
    name = image + ':' + tag
    command = [
        'docker',
        'images',
        '--format', '{{.ID}}',
        name
    ]
    output = subprocess.check_output(command)
    return output != ''


def remote_image_exist(registry, image, tag):
    requests.packages.urllib3.disable_warnings()
    url = 'https://%(registry)s/v2/%(image)s/tags/list' % dict(registry=registry, image=image)
    response = requests.get(url=url, verify=False)
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
        output = subprocess.check_output(command + [image])
        if output == '':
            continue
        image_info = [json.loads(record) for record in output.splitlines()]
        images_info += [['none', info['name'], info['tag']] for info in image_info]

    return images_info


def get_remote_images_info(images, registry):
    requests.packages.urllib3.disable_warnings()
    images_info = []
    for image in images:
        url = 'https://%(registry)s/v2/%(image)s/tags/list' % dict(registry=registry, image=image)
        response = requests.get(url=url, verify=False)
        info = response.json()
        images_info += [[registry, image, tag] for tag in info['tags']]

    return images_info


def get_image_digest(registry, image, tag):
    requests.packages.urllib3.disable_warnings()
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


def generate_fqdn_image(registry, image, tag='latest'):
    fqdn_image = image
    if registry is not None:
        fqdn_image = registry + '/' + fqdn_image
    if tag is not None:
        fqdn_image = fqdn_image + ':' + tag
    return fqdn_image


def image_to_dockerfile(image):
    return 'Dockerfile.' + image


def dockerfile_to_image(dockerfile):
    return dockerfile.replace('Dockerfile.', '')
