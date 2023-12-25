from __future__ import print_function

import logging
import os
import os.path
import sys

from re import compile as compile_expression
import click
import six
import tabulate
from pkg_resources import get_distribution
from pbr import packaging

from skipper import git, builder
from skipper import runner
from skipper import utils
from skipper.builder import BuildOptions, Image


def _validate_publish(ctx, param, value):
    # pylint: disable=unused-argument
    if value:
        matcher = compile_expression(r'^((\d+)(-(\d+))?):((\d+)(-(\d+))?)$')

        for port_mapping in value:
            _validate_port(matcher, port_mapping)

    return value


def _validate_port(matcher, port_forwarding):
    match = matcher.match(port_forwarding)
    if not match:
        raise click.BadParameter("Publish need to be in format port:port or port-port:port-port")

    host_port_start_range, host_port_end_range, container_port_start_range, container_port_end_range = match.group(2, 4, 6, 8)
    _validate_port_out_of_range(host_port_start_range)
    _validate_port_out_of_range(host_port_end_range)
    _validate_port_out_of_range(container_port_start_range)
    _validate_port_out_of_range(container_port_end_range)
    _validate_port_range(host_port_start_range, host_port_end_range)
    _validate_port_range(container_port_start_range, container_port_end_range)


def _validate_port_range(start, end):
    if start and end and end < start:
        raise click.BadParameter(f"Invalid port range: {start} should be bigger than {end}")


def _validate_port_out_of_range(port):
    if port and not 1 <= int(port) <= 65535:
        raise click.BadParameter(f"Invalid port number: port {port} is out of range")


# pylint: disable=too-many-arguments
@click.group()
@click.option('-v', '--verbose', help='Increase verbosity', is_flag=True, default=False)
@click.option('--registry', help='URL of the docker registry')
@click.option('--build-container-image', help='Image to use as build container')
@click.option('--build-container-tag', help='Tag of the build container')
@click.option('--build-container-net', help='Network to connect the build container')
@click.option('--env-file', multiple=True, help='Environment variable file(s) to load')
@click.option('--build-arg', multiple=True, help='Build arguments to pass to the container build', envvar='SKIPPER_BUILD_ARGS')
@click.option('--build-context', multiple=True, help='Build contexts to pass to the container build')
@click.pass_context
def cli(
        ctx,
        registry,
        build_container_image,
        build_container_tag,
        build_container_net,
        verbose,
        env_file,
        build_arg,
        build_context,
):
    """
    Easily dockerize your Git repository
    """
    logging_level = logging.DEBUG if verbose else logging.INFO
    utils.configure_logging(name='skipper', level=logging_level)
    ctx.obj['registry'] = registry
    ctx.obj['env_file'] = env_file
    ctx.obj['build_container_image'] = build_container_image
    ctx.obj['build_container_net'] = build_container_net
    ctx.obj['git_revision'] = build_container_tag == 'git:revision'
    ctx.obj['build_container_tag'] = (git.get_hash() if ctx.obj['git_revision'] else build_container_tag)
    ctx.obj['env'] = ctx.default_map.get('env', {})
    ctx.obj['containers'] = ctx.default_map.get('containers')
    ctx.obj['volumes'] = ctx.default_map.get('volumes')
    ctx.obj['workdir'] = ctx.default_map.get('workdir')
    ctx.obj['workspace'] = ctx.default_map.get('workspace', None)
    ctx.obj['container_context'] = ctx.default_map.get('container_context')
    ctx.obj['build_args'] = build_arg
    ctx.obj['build_contexts'] = build_context
    utils.set_remote_registry_login_info(registry, ctx.obj)


@cli.command()
@click.argument('images_to_build', nargs=-1, metavar='[IMAGE...]')
@click.option('--container-context', help='Container context path', default=None)
@click.option('-c', '--cache', help='Use cache image', is_flag=True, default=False, envvar='SKIPPER_USE_CACHE_IMAGE')
@click.pass_context
def build(ctx, images_to_build, container_context, cache):
    """
    Build a container
    """
    utils.logger.debug("Executing build command")

    valid_images_to_build = _get_images_to_build(ctx, images_to_build)
    tag = git.get_hash()
    build_args = (ctx.obj.get('build_args', ()) + (f'TAG={tag}',))
    build_contexts = ctx.obj.get('build_contexts', ())

    for image, dockerfile in valid_images_to_build.items():
        utils.logger.info("Building image: %s", image)

        main_context = container_context or ctx.obj.get('container_context') or os.path.dirname(dockerfile)
        options = BuildOptions(
            Image(name=image, tag=tag, dockerfile=dockerfile),
            main_context,
            build_contexts,
            build_args,
            cache,
        )

        ret = builder.build(options, runner.run, utils.logger)
        if ret != 0:
            utils.logger.error("Failed to build image: %s", options.image)
            return ret

    return 0


@cli.command()
@click.option('--namespace', help='Namespace to push into')
@click.option('--force', help="Push image even if it's already in the registry", is_flag=True, default=False)
@click.option('--pbr', help="Use PBR to tag the image", is_flag=True, default=False)
@click.argument('image')
@click.pass_context
def push(ctx, namespace, force, pbr, image):
    """
    Push a container
    """
    utils.logger.debug("Executing push command")
    _validate_global_params(ctx, 'registry')
    tag = git.get_hash()
    tag_to_push = tag
    if pbr:
        # Format = pbr_version.short_hash
        # pylint: disable=protected-access
        tag_to_push = f"{packaging._get_version_from_git().replace('dev', '')}.{tag[:8]}"
    image_name = image + ':' + tag

    ret = _push(ctx, force, image, image_name, namespace, tag_to_push)
    if ret != 0:
        return ret
    return ret


def _push(ctx, force, image, image_name, namespace, tag):
    fqdn_image = utils.generate_fqdn_image(ctx.obj['registry'], namespace, image, tag)
    utils.logger.debug("Adding tag %s", fqdn_image)
    command = ['tag', image_name, fqdn_image]
    ret = runner.run(command)
    if ret != 0:
        utils.logger.error('Failed to tag image: %s as fqdn: %s', image_name, fqdn_image)
        sys.exit(ret)
    repo_name = utils.generate_fqdn_image(None, namespace, image, tag=None)
    images_info = utils.get_remote_images_info([repo_name], ctx.obj['registry'],
                                               ctx.obj.get('username'), ctx.obj.get('password'))
    tags = [info[-1] for info in images_info]
    if tag in tags:
        if not force:
            utils.logger.info("Image %s is already in registry %s, not pushing",
                              fqdn_image, ctx.obj['registry'])
        else:
            utils.logger.warning("Image %s is already in registry %s, pushing anyway",
                                 fqdn_image, ctx.obj['registry'])
            _push_to_registry(ctx.obj['registry'], fqdn_image)
    else:
        _push_to_registry(ctx.obj['registry'], fqdn_image)
    utils.logger.debug("Removing tag %s", fqdn_image)
    command = ['rmi', fqdn_image]
    ret = runner.run(command)
    if ret != 0:
        utils.logger.warning('Failed to remove image tag: %s', fqdn_image)
    return ret


@cli.command()
@click.option('-r', '--remote', help='List also remote images', is_flag=True, default=False)
@click.pass_context
def images(ctx, remote):
    """
    List images
    """
    utils.logger.debug("Executing images command")

    valid_images = ctx.obj.get('containers') or utils.get_images_from_dockerfiles()
    images_names = valid_images.keys()
    utils.logger.info("Expected images: %s\n", ", ".join(images_names))
    images_info = utils.get_local_images_info(images_names)
    if remote:
        _validate_global_params(ctx, 'registry')
        try:
            images_info += utils.get_remote_images_info(images_names, ctx.obj['registry'],
                                                        ctx.obj.get('username'), ctx.obj.get('password'))
        except Exception as exp:
            raise click.exceptions.ClickException(f'Got unknown error from remote registry {exp}')

    print(tabulate.tabulate(images_info, headers=['REGISTRY', 'IMAGE', 'TAG'], tablefmt='grid'))


@cli.command()
@click.option('-r', '--remote', help='Delete image from registry', is_flag=True, default=False)
@click.argument('image')
@click.argument('tag')
@click.pass_context
def rmi(ctx, remote, image, tag):
    """
    Delete an image from local docker or from registry
    """
    utils.logger.debug("Executing rmi command")
    _validate_project_image(image)
    if remote:
        _validate_global_params(ctx, 'registry')
        utils.delete_image_from_registry(ctx.obj['registry'], image, tag,
                                         ctx.obj.get('username'), ctx.obj.get('password'))
    else:
        utils.delete_local_image(image, tag)


@cli.command(context_settings={"ignore_unknown_options": True})
@click.option('-i', '--interactive', help='Interactive mode', is_flag=True, default=False, envvar='SKIPPER_INTERACTIVE')
@click.option('-n', '--name', help='Container name', default=None)
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.option('-c', '--cache', help='Use cache image', is_flag=True, default=False, envvar='SKIPPER_USE_CACHE_IMAGE')
@click.option('-p', '--publish', multiple=True, help="Publish a port", callback=_validate_publish)
@click.argument('command', nargs=-1, type=click.UNPROCESSED, required=True)
@click.pass_context
def run(ctx, interactive, name, env, publish, cache, command):
    """
    Run arbitrary commands
    """
    utils.logger.debug("Executing run command")
    _validate_global_params(ctx, 'build_container_image')
    ctx.obj['use_cache'] = cache

    build_container = _prepare_build_container(
        BuildOptions.from_context_obj(ctx.obj),
        ctx.obj.get('git_revision'),
        ctx.obj.get('username'),
        ctx.obj.get('password'),
    )

    return runner.run(
        list(command),
        fqdn_image=build_container,
        environment=_expend_env(ctx, env),
        interactive=interactive,
        name=name,
        net=ctx.obj['build_container_net'],
        publish=publish,
        volumes=ctx.obj.get('volumes'),
        workdir=ctx.obj.get('workdir'),
        use_cache=cache,
        workspace=ctx.obj.get('workspace'),
        env_file=ctx.obj.get('env_file'),
    )


@cli.command(context_settings={"ignore_unknown_options": True})
@click.option('-i', '--interactive', help='Interactive mode', is_flag=True, default=False, envvar='SKIPPER_INTERACTIVE')
@click.option('-n', '--name', help='Container name', default=None)
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.option('-f', 'makefile', help='Makefile to use', default='Makefile')
@click.option('-c', '--cache', help='Use cache image', is_flag=True, default=False, envvar='SKIPPER_USE_CACHE_IMAGE')
@click.option('-p', '--publish', multiple=True, help="Publish a port", callback=_validate_publish)
@click.argument('make_params', nargs=-1, type=click.UNPROCESSED, required=False)
@click.pass_context
def make(ctx, interactive, name, env, makefile, cache, publish, make_params):
    """
    Execute makefile target(s)
    """
    utils.logger.debug("Executing make command")
    _validate_global_params(ctx, 'build_container_image')
    ctx.obj['use_cache'] = cache

    build_container = _prepare_build_container(
        BuildOptions.from_context_obj(ctx.obj),
        ctx.obj.get('git_revision'),
        ctx.obj.get('username'),
        ctx.obj.get('password'),
    )

    command = ['make', '-f', makefile] + list(make_params)
    return runner.run(
        command,
        fqdn_image=build_container,
        environment=_expend_env(ctx, env),
        interactive=interactive,
        name=name,
        net=ctx.obj['build_container_net'],
        publish=publish,
        volumes=ctx.obj.get('volumes'),
        workdir=ctx.obj.get('workdir'),
        use_cache=cache,
        workspace=ctx.obj.get('workspace'),
        env_file=ctx.obj.get('env_file'),
    )


@cli.command()
@click.option('-e', '--env', multiple=True, help='Environment variables to pass the container')
@click.option('-n', '--name', help='Container name', default=None)
@click.option('-c', '--cache', help='Use cache image', is_flag=True, default=False, envvar='SKIPPER_USE_CACHE_IMAGE')
@click.option('-p', '--publish', multiple=True, help="Publish a port", callback=_validate_publish)
@click.pass_context
def shell(ctx, env, name, cache, publish):
    """
    Start a shell
    """
    utils.logger.debug("Starting a shell")
    _validate_global_params(ctx, 'build_container_image')
    ctx.obj['use_cache'] = cache

    build_container = _prepare_build_container(
        BuildOptions.from_context_obj(ctx.obj),
        ctx.obj.get('git_revision'),
        ctx.obj.get('username'),
        ctx.obj.get('password'),
    )

    return runner.run(
        ['bash'],
        fqdn_image=build_container,
        environment=_expend_env(ctx, env),
        interactive=True,
        name=name,
        net=ctx.obj['build_container_net'],
        publish=publish,
        volumes=ctx.obj.get('volumes'),
        workdir=ctx.obj.get('workdir'),
        use_cache=cache,
        workspace=ctx.obj.get('workspace'),
        env_file=ctx.obj.get('env_file'),
    )


@cli.command()
def version():
    """
    output skipper version
    """
    utils.logger.debug("printing skipper version")
    click.echo(get_distribution("strato-skipper").version)  # pylint: disable=no-member


@cli.command()
def completion():
    """
    output bash completion script
    """
    completion_file_path = utils.get_extra_file("skipper-complete.sh")

    with open(completion_file_path, 'r') as fin:
        print(fin.read(), end="")


def _push_to_registry(registry, fqdn_image):
    utils.logger.debug("Pushing to registry %s", registry)
    command = ['push', fqdn_image]
    ret = runner.run(command)
    if ret != 0:
        utils.logger.error('Failed to push image: %s', fqdn_image)
        sys.exit(ret)


def _prepare_build_container(
        options: BuildOptions,
        git_revision: bool,
        username: str,
        password: str,
):
    def runner_run(command):
        """
        All output generated by the container runtime during this stage should
        not be included in stdout - we should redirect it to stderr, as the
        user is just using skipper as a wrapper to run commands like make, run
        etc - they don't care that as a side-effect of running their commands a
        container is being built, and they don't want the output from that
        build process to be included in the stdout for the commands they wrap
        with skipper.

        This allows users to do things like VERSION=$(skipper make get_version)
        without having the build process output be included in their VERSION
        env var.
        """
        utils.logger.debug("Running command: %s", command)
        return runner.run(command, stdout_to_stderr=True)

    image = options.image

    if image.tag:
        if utils.local_image_exist(image.name, image.tag):
            utils.logger.info('Using build container: %s', image.name)
            return image.local

        if image.registry and utils.remote_image_exist(image.registry, image.name, image.tag, username, password):
            utils.logger.info('Using build container: %s', image.fqdn)
            return image.fqdn

        if not git_revision:
            raise click.exceptions.ClickException(f"Couldn't find build image {image.name} with tag {image.tag}")
    else:
        utils.logger.info('No build container tag was provided')

    if not image.dockerfile:
        sys.exit(f'Could not find any dockerfile for {image.name}')

    utils.logger.info('Building image using docker file: %s', image.dockerfile)

    if builder.build(options, runner_run, utils.logger) != 0:
        sys.exit(f'Failed to build image: {image}')

    return image.local


def _validate_global_params(ctx, *params):
    for param in params:
        if ctx.obj[param] is None:
            raise click.BadParameter(str(ctx.obj[param]), param_hint=param)


def _validate_project_image(image):
    project_images = utils.get_images_from_dockerfiles()
    if image not in project_images:
        raise click.BadParameter(f"'{image}' is not an image of this project, try {project_images}", param_hint='image')


def _expend_env(ctx, extra_env):
    environment = []
    env = ctx.obj['env']
    # env is allowed to be of type list and of type dict
    if isinstance(env, dict):
        for key, value in six.iteritems(env):
            utils.logger.debug("Adding %s=%s to environment", key, value)
            environment.append(f"{key}={value}")
    elif isinstance(env, list):
        for item in env:
            if '=' in item:
                # if the items is of the form 'a=b', add it to the environment list
                environment.append(item)
            else:
                # if the items is just a name of environment variable, try to get it
                # from the host's environment variables
                if item in os.environ:
                    environment.append(f'{item}={os.environ[item]}')
    else:
        raise TypeError(f'Type {type(env)} not supported for key env, use dict or list instead')

    return environment + list(extra_env)


def _get_images_to_build(ctx, images_to_build):
    valid_images = ctx.obj.get('containers') or utils.get_images_from_dockerfiles()
    valid_images = {
        image: os.path.abspath(dockerfile) for image, dockerfile in valid_images.items()
    }
    valid_images_to_build = {}
    if not images_to_build:
        valid_images_to_build = valid_images
    else:
        for image in images_to_build:
            if image not in valid_images:
                utils.logger.warning("Image %s is not valid for this project! Skipping...", image)
                continue
            if not os.path.exists(valid_images[image]):
                utils.logger.warning("Dockerfile %s does not exist! Skipping...", valid_images[image])
                continue
            valid_images_to_build[image] = valid_images[image]
    return valid_images_to_build
