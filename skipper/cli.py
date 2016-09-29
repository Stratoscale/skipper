import logging
import subprocess
import tabulate
import click
from skipper import git
from skipper import runner
from skipper import utils


@click.group()
@click.option('-v', '--verbose', help='Increase verbosity', is_flag=True, default=False)
@click.option('--registry', help='URL of the docker registry')
@click.option('--build-container-image', help='Image to use as build container')
@click.option('--build-container-tag', help='Tag of the build container')
@click.pass_context
def cli(ctx, registry, build_container_image, build_container_tag, verbose):
    '''
    Easily dockerize your Git repository
    '''
    logging_level = logging.DEBUG if verbose else logging.INFO
    utils.configure_logging(name='skipper', level=logging_level)

    ctx.obj['registry'] = registry
    ctx.obj['build_container_image'] = build_container_image
    ctx.obj['build_container_tag'] = build_container_tag
    ctx.obj['env'] = ctx.default_map.get('env', {})


@cli.command()
@click.argument('images_to_build', nargs=-1, metavar='[IMAGE...]')
@click.pass_context
def build(ctx, images_to_build):
    '''
    Build a container
    '''
    utils.logger.debug("Executing build command")
    _validate_global_params(ctx, 'registry')
    images_to_build = images_to_build or utils.get_images_from_dockerfiles()
    tag = git.get_hash()
    for image in images_to_build:
        utils.logger.info('Building image: %(image)s', dict(image=image))
        dockerfile = utils.image_to_dockerfile(image)
        fqdn_image = utils.generate_fqdn_image(ctx.obj['registry'], image, tag)

        command = [
            'docker',
            'build',
            '-f', dockerfile,
            '-t', fqdn_image,
            '.'
        ]

        ret = runner.run(command)
        if ret != 0:
            utils.logger.error('Failed to build image: %(image)s', dict(image=image))
            return ret

    return 0


@cli.command()
@click.argument('image')
@click.pass_context
def push(ctx, image):
    '''
    Push a container
    '''
    utils.logger.debug("Executing push command")
    _validate_global_params(ctx, 'registry')
    tag = git.get_hash()
    fqdn_image = utils.generate_fqdn_image(ctx.obj['registry'], image, tag)

    command = [
        'docker',
        'push',
        fqdn_image
    ]

    return runner.run(command)


@cli.command()
@click.option('-r', '--remote', help='List also remote images', is_flag=True, default=False)
@click.pass_context
def images(ctx, remote):
    '''
    List images
    '''
    utils.logger.debug("Executing images command")
    _validate_global_params(ctx, 'registry')
    images_names = utils.get_images_from_dockerfiles()
    images_info = utils.get_local_images_info(images_names, ctx.obj['registry'])
    if remote:
        images_info += utils.get_remote_images_info(images_names, ctx.obj['registry'])

    print(tabulate.tabulate(images_info, headers=['ORIGIN', 'IMAGE', 'TAG'], tablefmt='grid'))


@cli.command()
@click.option('-r', '--remote', help='Delete image from registry', is_flag=True, default=False)
@click.argument('image')
@click.argument('tag')
@click.pass_context
def rmi(ctx, remote, image, tag):
    '''
    Delete an image from local docker or from registry
    '''
    utils.logger.debug("Executing rmi command")
    _validate_global_params(ctx, 'registry')
    _validate_project_image(image)
    if remote:
        utils.delete_image_from_registry(ctx.obj['registry'], image, tag)
    else:
        utils.delete_local_image(ctx.obj['registry'], image, tag)


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.argument('command', nargs=-1, type=click.UNPROCESSED, required=True)
@click.pass_context
def run(ctx, env, command):
    '''
    Run arbitrary commands
    '''
    utils.logger.debug("Executing run command")
    _validate_global_params(ctx, 'build_container_image')
    build_container = _prepare_build_container(ctx.obj['registry'],
                                               ctx.obj['build_container_image'],
                                               ctx.obj['build_container_tag'])
    return runner.run(list(command), fqdn_image=build_container, environment=_expend_env(ctx, env))


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.option('-f', 'makefile', help='Makefile to use', default='Makefile')
@click.argument('target')
@click.pass_context
def make(ctx, env, makefile, target):
    '''
    Execute makefile target
    '''
    utils.logger.debug("Executing make command")
    _validate_global_params(ctx, 'build_container_image')
    build_container = _prepare_build_container(ctx.obj['registry'],
                                               ctx.obj['build_container_image'],
                                               ctx.obj['build_container_tag'])
    command = [
        'make',
        '-f', makefile,
        target
    ]
    return runner.run(command, fqdn_image=build_container, environment=_expend_env(ctx, env))


@cli.command()
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.pass_context
def shell(ctx, env):
    '''
    Start a shell
    '''
    utils.logger.debug("Starting a shell")
    _validate_global_params(ctx, 'build_container_image')
    build_container = _prepare_build_container(ctx.obj['registry'],
                                               ctx.obj['build_container_image'],
                                               ctx.obj['build_container_tag'])
    return runner.run(['bash'], fqdn_image=build_container, environment=_expend_env(ctx, env), interactive=True)


def _prepare_build_container(registry, image, tag):
    if tag is not None:
        fqdn_image = utils.generate_fqdn_image(registry, image, tag)
        utils.logger.info("Using build container: %(fqdn_image)s", dict(fqdn_image=fqdn_image))
        return fqdn_image

    utils.logger.info("No build container tag was provided. Building from scratch...")
    dockerfile = utils.image_to_dockerfile(image)
    command = [
        'docker',
        'build',
        '-q',
        '-f', dockerfile,
        '.'
    ]

    return subprocess.check_output(command).strip()


def _validate_global_params(ctx, *params):
    for param in params:
        if ctx.obj[param] is None:
            raise click.BadParameter(str(ctx.obj[param]), param_hint=param)


def _validate_project_image(image):
    project_images = utils.get_images_from_dockerfiles()
    if image not in project_images:
        raise click.BadParameter("'%s' is not an image of this project, try %s" % (image, project_images), param_hint='image')


def _expend_env(ctx, extra_env):
    environment = []
    for key, value in ctx.obj['env'].iteritems():
        utils.logger.debug("Adding {}={} to environment".format(key, value))
        environment.append("{}={}".format(key, value))
    return environment + list(extra_env)
