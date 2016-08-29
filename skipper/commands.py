import logging
import click
from skipper import runner
from skipper import git


@click.group()
@click.option('-q', '--quiet', help='Silence the output', is_flag=True, default=False)
@click.option('--nested/--no-nested', help='Run inside a contanier', default=True)
@click.option('--registry', help='URL of the docker registry')
@click.option('--image', help='Image to use as build container')
@click.option('--tag', help='Tag of the build container')
@click.pass_context
def cli(ctx, registry, image, tag, quiet, nested):
    '''
    Easily dockerize your Git repository
    '''
    logging_level = logging.INFO if quiet else logging.DEBUG
    logging.basicConfig(format='%(message)s', level=logging_level)

    ctx.obj['registry'] = registry
    if nested:
        ctx.obj['fqdn_image'] = _generate_fqdn_image(registry, image, tag)
    else:
        ctx.obj['fqdn_image'] = None


@cli.command()
@click.argument('image')
@click.pass_context
def build(ctx, image):
    '''
    Builds a container
    '''
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

    runner.run(command, fqdn_image=ctx.obj['fqdn_image'])


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.argument('command', nargs=-1, type=click.UNPROCESSED, required=True)
@click.pass_context
def run(ctx, env, command):
    '''
    Runs arbitrary commands
    '''
    return runner.run(list(command), fqdn_image=ctx.obj['fqdn_image'], environment=list(env))


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.option('-f', 'makefile', help='Tag of the image')
@click.argument('target')
@click.pass_context
def make(ctx, env, makefile, target):
    '''
    Executes makefile target
    '''
    command = [
        'make',
        '-f', makefile,
        target
    ]
    return runner.run(command, fqdn_image=ctx.obj['fqdn_image'], environment=list(env))


def _generate_fqdn_image(registry, image, tag='latest'):
    return registry + '/' + image + ':' + tag
