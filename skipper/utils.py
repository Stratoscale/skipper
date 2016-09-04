import logging


def configure_logging(name, level):
    logger = logging.getLogger(name)

    formatter = logging.Formatter('[%(name)s] %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(console_handler)


def generate_fqdn_image(registry, image, tag='latest'):
    fqdn_image = image
    if registry is not None:
        fqdn_image = registry + '/' + fqdn_image
    if tag is not None:
        fqdn_image = fqdn_image + ':' + tag
    return fqdn_image
