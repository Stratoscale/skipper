import logging
import click
from skipper import runner
from skipper import git


@click.group()
@click.option('-q', '--quiet', help='Silence the output', is_flag=True, default=False)
@click.option('--nested/--no-nested', help='Run inside a build contanier', default=True)
@click.option('--registry', help='URL of the docker registry')
@click.option('--build-container-image', help='Image to use as build container')
@click.option('--build-container-tag', help='Tag of the build container')
@click.pass_context
def cli(ctx, registry, build_container_image, build_container_tag, quiet, nested):
    '''
    Easily dockerize your Git repository
    '''
    logging_level = logging.INFO if quiet else logging.DEBUG
    logging.basicConfig(format='%(message)s', level=logging_level)

    ctx.obj['nested'] = nested
    ctx.obj['registry'] = registry
    ctx.obj['build_container_image'] = build_container_image
    ctx.obj['build_container_tag'] = build_container_tag


@cli.command()
@click.argument('image')
@click.pass_context
def build(ctx, image):
    '''
    Builds a container
    '''
    build_container = _get_build_container_from_ctx(ctx)
    dockerfile = image + '.Dockerfile'
    tag = git.get_hash()
    fqdn_image = _generate_fqdn_image(ctx.obj['registry'], image, tag)

    command = [
        "docker",
        "build",
        "-f", dockerfile,
        "-t", fqdn_image,
        '.'
    ]

    runner.run(command, fqdn_image=build_container)


@cli.command()
@click.argument('image')
@click.pass_context
def push(ctx, image):
    '''
    Pushes a container
    '''
    build_container = _get_build_container_from_ctx(ctx)
    tag = git.get_hash()
    fqdn_image = _generate_fqdn_image(ctx.obj['registry'], image, tag)

    command = [
        'docker',
        'push',
        fqdn_image
    ]

    runner.run(command, fqdn_image=build_container)


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.argument('command', nargs=-1, type=click.UNPROCESSED, required=True)
@click.pass_context
def run(ctx, env, command):
    '''
    Runs arbitrary commands
    '''
    build_container = _get_build_container_from_ctx(ctx)
    return runner.run(list(command), fqdn_image=build_container, environment=list(env))


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.option('-f', 'makefile', help='Makefile to use')
@click.argument('target')
@click.pass_context
def make(ctx, env, makefile, target):
    '''
    Executes makefile target
    '''
    build_container = _get_build_container_from_ctx(ctx)
    command = [
        'make',
        '-f', makefile,
        target
    ]
    return runner.run(command, fqdn_image=build_container, environment=list(env))


def _generate_fqdn_image(registry, image, tag='latest'):
    return registry + '/' + image + ':' + tag


def _get_build_container_from_ctx(ctx):
    build_container = None
    if ctx.obj['nested']:
        try:
            build_container = _generate_fqdn_image(
                ctx.obj['registry'],
                ctx.obj['build_container_image'],
                ctx.obj['build_container_tag']
            )
        except:
            raise click.BadParameter('At least one of the parameters: regitstry, build_container_image or build_container_tag is invalid')

    return build_container
