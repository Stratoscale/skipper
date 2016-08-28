import grp
import logging
import os
import click
from skipper import docker
from skipper import git


@click.group()
@click.option('-q', '--quiet', help='Silence the output', is_flag=True, default=False)
def cli(quiet):
    '''
    Easily dockerize your Git repository
    '''

    logging_level = logging.INFO if quiet else logging.DEBUG
    logging.basicConfig(format='%(message)s', level=logging_level)


@cli.command()
@click.option('--registry', help='URL of the docker registry')
@click.option('--image', help='Image to build')
@click.option('--tag', help='Tag of the image')
def build(registry, image, tag=None):
    '''
    Builds a containers
    '''
    dockerfile = image + '.Dockerfile'
    workspace = os.getcwd()
    tag = tag or git.get_hash()
    fqdn_image = _generate_fqdn_image(registry, image, tag)
    docker.build(workspace, dockerfile, fqdn_image)


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('--registry', help='URL of the docker registry')
@click.option('--image', help='Image to build')
@click.option('--tag', help='Tag of the image')
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.argument('command', nargs=-1, type=click.UNPROCESSED)
def run(registry, image, tag, env, command):
    '''
    Runs commands inside a container
    '''
    fqdn_image = _generate_fqdn_image(registry, image, tag)

    cwd = os.getcwd()
    workspace = os.path.dirname(cwd)
    project = os.path.basename(cwd)

    uid = os.getuid()
    gid = grp.getgrnam('docker').gr_gid

    if len(command) == 0:
        logging.error('Command was not provided')
    else:
        return docker.run(workspace, project, uid, gid, fqdn_image, list(env), list(command))


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('--registry', help='URL of the docker registry')
@click.option('--image', help='Image to build')
@click.option('--tag', help='Tag of the image')
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.option('-f', 'makefile', help='Tag of the image')
@click.argument('target')
def make(registry, image, tag, env, makefile, target):
    '''
    Executes makefile target
    '''
    command = ['make', '-f', makefile, target]
    fqdn_image = _generate_fqdn_image(registry, image, tag)

    cwd = os.getcwd()
    workspace = os.path.dirname(cwd)
    project = os.path.basename(cwd)

    uid = os.getuid()
    gid = grp.getgrnam('docker').gr_gid

    return docker.run(workspace, project, uid, gid, fqdn_image, list(env), list(command))


def _generate_fqdn_image(registry, image, tag='latest'):
    return registry + '/' + image + ':' + tag
