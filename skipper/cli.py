import sys
import logging
import os.path
import tabulate
import click
import six
from pkg_resources import get_distribution
from skipper import git
from skipper import runner
from skipper import utils


@click.group()
@click.option('-v', '--verbose', help='Increase verbosity', is_flag=True, default=False)
@click.option('--registry', help='URL of the docker registry')
@click.option('--build-container-image', help='Image to use as build container')
@click.option('--build-container-tag', help='Tag of the build container')
@click.option('--build-container-net', help='Network to connect the build container', default='host')
@click.pass_context
def cli(ctx, registry, build_container_image, build_container_tag, build_container_net, verbose):
    '''
    Easily dockerize your Git repository
    '''
    logging_level = logging.DEBUG if verbose else logging.INFO
    utils.configure_logging(name='skipper', level=logging_level)

    ctx.obj['registry'] = registry
    ctx.obj['build_container_image'] = build_container_image
    ctx.obj['build_container_net'] = build_container_net
    ctx.obj['git_revision'] = build_container_tag == 'git:revision'
    ctx.obj['build_container_tag'] = git.get_hash() if ctx.obj['git_revision'] else build_container_tag
    ctx.obj['env'] = ctx.default_map.get('env', {})
    ctx.obj['containers'] = ctx.default_map.get('containers')
    ctx.obj['volumes'] = ctx.default_map.get('volumes')
    ctx.obj['workdir'] = ctx.default_map.get('workdir')
    ctx.obj['container_context'] = ctx.default_map.get('container_context')


@cli.command()
@click.argument('images_to_build', nargs=-1, metavar='[IMAGE...]')
@click.option('--container-context', help='Container context path', default=None)
@click.pass_context
def build(ctx, images_to_build, container_context):
    '''
    Build a container
    '''
    utils.logger.debug("Executing build command")

    valid_images = ctx.obj.get('containers') or utils.get_images_from_dockerfiles()
    valid_images = {image: os.path.abspath(dockerfile) for image, dockerfile in six.iteritems(valid_images)}
    valid_images_to_build = {}
    if not images_to_build:
        valid_images_to_build = valid_images
    else:
        for image in images_to_build:
            if image not in valid_images:
                utils.logger.warning('Image %(image)s is not valid for this project! Skipping...', dict(image=image))
                continue
            valid_images_to_build[image] = valid_images[image]

    tag = git.get_hash()
    for image, dockerfile in six.iteritems(valid_images_to_build):
        utils.logger.info('Building image: %(image)s', dict(image=image))

        if not os.path.exists(dockerfile):
            utils.logger.warning('Dockerfile %(dockerfile)s does not exist! Skipping...', dict(dockerfile=dockerfile))
            continue

        fqdn_image = image + ':' + tag
        if container_context is not None:
            build_context = container_context
        elif ctx.obj['container_context']:
            build_context = ctx.obj['container_context']
        else:
            build_context = os.path.dirname(dockerfile)
        command = ['docker', 'build', '-f', dockerfile, '-t', fqdn_image, build_context]
        ret = runner.run(command)

        if ret != 0:
            utils.logger.error('Failed to build image: %(image)s', dict(image=image))
            return ret

    return 0


@cli.command()
@click.option('--namespace', help='Namespace to push into')
@click.argument('image')
@click.pass_context
def push(ctx, namespace, image):
    '''
    Push a container
    '''
    utils.logger.debug("Executing push command")
    _validate_global_params(ctx, 'registry')
    tag = git.get_hash()
    image_name = image + ':' + tag
    fqdn_image = utils.generate_fqdn_image(ctx.obj['registry'], namespace, image, tag)

    utils.logger.debug("Adding tag %(tag)s", dict(tag=fqdn_image))
    command = ['docker', 'tag', image_name, fqdn_image]
    ret = runner.run(command)
    if ret != 0:
        utils.logger.error('Failed to tag image: %(tag)s as fqdn', dict(tag=image_name, fqdn=fqdn_image))
        sys.exit(ret)

    utils.logger.debug("Pushing to registry %(registry)s", dict(registry=ctx.obj['registry']))
    command = ['docker', 'push', fqdn_image]
    ret = runner.run(command)
    if ret != 0:
        utils.logger.error('Failed to push image: %(tag)s', dict(tag=fqdn_image))
        sys.exit(ret)

    utils.logger.debug("Removing tag %(tag)s", dict(tag=fqdn_image))
    command = ['docker', 'rmi', fqdn_image]
    ret = runner.run(command)
    if ret != 0:
        utils.logger.warning('Failed to remove image tag: %(tag)s', dict(tag=fqdn_image))
    return ret


@cli.command()
@click.option('-r', '--remote', help='List also remote images', is_flag=True, default=False)
@click.pass_context
def images(ctx, remote):
    '''
    List images
    '''
    utils.logger.debug("Executing images command")

    valid_images = ctx.obj.get('containers') or utils.get_images_from_dockerfiles()
    images_names = valid_images.keys()
    utils.logger.info("Expected images: %(images)s\n", dict(images=", ".join(images_names)))
    images_info = utils.get_local_images_info(images_names)
    if remote:
        _validate_global_params(ctx, 'registry')
        try:
            images_info += utils.get_remote_images_info(images_names, ctx.obj['registry'])
        except Exception as exp:
            raise click.exceptions.ClickException('Got unknow error from remote registry %(error)s' % dict(error=exp.message))

    print(tabulate.tabulate(images_info, headers=['REGISTRY', 'IMAGE', 'TAG'], tablefmt='grid'))


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
    _validate_project_image(image)
    if remote:
        _validate_global_params(ctx, 'registry')
        utils.delete_image_from_registry(ctx.obj['registry'], image, tag)
    else:
        utils.delete_local_image(image, tag)


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('-i', '--interactive', help='Interactive mode', is_flag=True, default=False, envvar='SKIPPER_INTERACTIVE')
@click.option('-n', '--name', help='Container name', default=None)
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.argument('command', nargs=-1, type=click.UNPROCESSED, required=True)
@click.pass_context
def run(ctx, interactive, name, env, command):
    '''
    Run arbitrary commands
    '''
    utils.logger.debug("Executing run command")
    _validate_global_params(ctx, 'build_container_image')
    build_container = _prepare_build_container(ctx.obj['registry'],
                                               ctx.obj['build_container_image'],
                                               ctx.obj['build_container_tag'],
                                               ctx.obj['git_revision'],
                                               ctx.obj['container_context'])
    return runner.run(list(command),
                      fqdn_image=build_container,
                      environment=_expend_env(ctx, env),
                      interactive=interactive,
                      name=name,
                      net=ctx.obj['build_container_net'],
                      volumes=ctx.obj.get('volumes'),
                      workdir=ctx.obj.get('workdir'))


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.option('-i', '--interactive', help='Interactive mode', is_flag=True, default=False, envvar='SKIPPER_INTERACTIVE')
@click.option('-n', '--name', help='Container name', default=None)
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.option('-f', 'makefile', help='Makefile to use', default='Makefile')
@click.argument('make_params', nargs=-1, type=click.UNPROCESSED, required=False)
@click.pass_context
def make(ctx, interactive, name, env, makefile, make_params):
    '''
    Execute makefile target(s)
    '''
    utils.logger.debug("Executing make command")
    _validate_global_params(ctx, 'build_container_image')
    build_container = _prepare_build_container(ctx.obj['registry'],
                                               ctx.obj['build_container_image'],
                                               ctx.obj['build_container_tag'],
                                               ctx.obj['git_revision'],
                                               ctx.obj['container_context'])
    command = ['make', '-f', makefile] + list(make_params)
    return runner.run(command,
                      fqdn_image=build_container,
                      environment=_expend_env(ctx, env),
                      interactive=interactive,
                      name=name,
                      net=ctx.obj['build_container_net'],
                      volumes=ctx.obj.get('volumes'),
                      workdir=ctx.obj.get('workdir'))


@cli.command()
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.option('-n', '--name', help='Container name', default=None)
@click.pass_context
def shell(ctx, env, name):
    '''
    Start a shell
    '''
    utils.logger.debug("Starting a shell")
    _validate_global_params(ctx, 'build_container_image')
    build_container = _prepare_build_container(ctx.obj['registry'],
                                               ctx.obj['build_container_image'],
                                               ctx.obj['build_container_tag'],
                                               ctx.obj['git_revision'],
                                               ctx.obj['container_context'])
    return runner.run(['bash'],
                      fqdn_image=build_container,
                      environment=_expend_env(ctx, env),
                      interactive=True,
                      name=name,
                      net=ctx.obj['build_container_net'],
                      volumes=ctx.obj.get('volumes'),
                      workdir=ctx.obj.get('workdir'))


@cli.command()
def version():
    '''
    Output skipper version
    '''
    utils.logger.debug("Printing skipper version")
    click.echo(get_distribution("strato-skipper").version)  # pylint: disable=no-member


def _prepare_build_container(registry, image, tag, git_revision=False, container_context=None):

    if tag is not None:

        tagged_image_name = image + ':' + tag

        if utils.local_image_exist(image, tag):
            utils.logger.info("Using build container: %(image_name)s", dict(image_name=tagged_image_name))
            return tagged_image_name

        if utils.remote_image_exist(registry, image, tag):
            fqdn_image = utils.generate_fqdn_image(registry, None, image, tag)
            utils.logger.info("Using build container: %(fqdn_image)s", dict(fqdn_image=fqdn_image))
            return fqdn_image

        if not git_revision:
            raise click.exceptions.ClickException(
                "Couldn't find build image %(image)s with tag %(tag)s" % dict(image=image, tag=tag))

    else:
        tagged_image_name = image
        utils.logger.info("No build container tag was provided")

    docker_file = utils.image_to_dockerfile(image)
    utils.logger.info("Building image using docker file: %(docker_file)s", dict(docker_file=docker_file))
    if container_context is not None:
        build_context = container_context
    else:
        build_context = '.'
    ret = runner.run(['docker', 'build', '-t', image, '-f', docker_file, build_context])
    if ret != 0:
        exit('Failed to build image: %(image)s' % dict(image=image))

    if git_revision and not git.uncommitted_changes():
        utils.logger.info("Tagging image with git revision: %(tag)s", dict(tag=tag))
        runner.run(['docker', 'tag', image, tagged_image_name])

    return image


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
    for key, value in six.iteritems(ctx.obj['env']):
        utils.logger.debug("Adding %s=%s to environment", key, value)
        environment.append("{}={}".format(key, value))
    return environment + list(extra_env)
