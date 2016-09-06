import logging
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


@cli.command()
@click.argument('image')
@click.pass_context
def build(ctx, image):
    '''
    Build a container
    '''
    _validate_global_params(ctx, 'registry')
    dockerfile = utils.image_to_dockerfile(image)
    tag = git.get_hash()
    fqdn_image = utils.generate_fqdn_image(ctx.obj['registry'], image, tag)

    command = [
        'docker',
        'build',
        '-f', dockerfile,
        '-t', fqdn_image,
        '.'
    ]

    return runner.run(command)


@cli.command()
@click.argument('image')
@click.pass_context
def push(ctx, image):
    '''
    Push a container
    '''
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
    _validate_global_params(ctx, 'registry')
    images_names = utils.get_images_from_dockerfiles()
    images_info = utils.get_local_images_info(images_names, ctx.obj['registry'])
    if remote:
        images_info += utils.get_remote_images_info(images_names, ctx.obj['registry'])

    print(tabulate.tabulate(images_info, headers=['ORIGIN', 'IMAGE', 'TAG'], tablefmt='grid'))


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.argument('command', nargs=-1, type=click.UNPROCESSED, required=True)
@click.pass_context
def run(ctx, env, command):
    '''
    Run arbitrary commands
    '''
    _validate_global_params(ctx, 'registry', 'build_container_image', 'build_container_tag')
    build_container = _get_build_container_from_ctx(ctx)
    return runner.run(list(command), fqdn_image=build_container, environment=list(env))


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.option('-f', 'makefile', help='Makefile to use', default='Makefile')
@click.argument('target')
@click.pass_context
def make(ctx, env, makefile, target):
    '''
    Execute makefile target
    '''
    _validate_global_params(ctx, 'registry', 'build_container_image', 'build_container_tag')
    build_container = _get_build_container_from_ctx(ctx)
    command = [
        'make',
        '-f', makefile,
        target
    ]
    return runner.run(command, fqdn_image=build_container, environment=list(env))


def _get_build_container_from_ctx(ctx):
    build_container = utils.generate_fqdn_image(
        ctx.obj['registry'],
        ctx.obj['build_container_image'],
        ctx.obj['build_container_tag']
    )

    return build_container


def _validate_global_params(ctx, *params):
    for param in params:
        if ctx.obj[param] is None:
            raise click.BadParameter(str(ctx.obj[param]), param_hint=param)
