from dataclasses import dataclass
from logging import Logger
from typing import Callable

from skipper import utils

DOCKER_TAG_FOR_CACHE = "cache"


class Image:
    """
    A class to represent an image with attributes like registry, name, tag, namespace.
    """

    def __init__(self, name, tag, dockerfile=None, registry=None, namespace=None):
        """
        Constructs all the necessary attributes for the Image object.

        :param registry: Registry for the image
        :param name: Name of the image
        :param tag: Tag for the image
        :param namespace: Namespace for the registry
        """
        if not name:
            raise ValueError("Image name is required")

        self.name = name
        self.tag = tag
        self.registry = registry
        self.namespace = namespace
        self.__dockerfile = dockerfile
        self.__cache_fqdn = None
        self.__fqdn = None

    def __str__(self):
        return self.fqdn

    @property
    def local(self):
        """
        Creates a string that represents the local image.

        :return: Image in name:tag format
        """
        if self.tag:
            return self.name + ":" + self.tag
        return self.name

    @property
    def cache_fqdn(self):
        """
        Generates a Fully Qualified Domain Name for the cached image.

        :return: Cached image Fully Qualified Domain Name
        """
        if not self.__cache_fqdn:
            self.__cache_fqdn = utils.generate_fqdn_image(
                self.registry, self.namespace, self.name, DOCKER_TAG_FOR_CACHE
            )
        return self.__cache_fqdn

    @property
    def fqdn(self):
        """
        Generates a Fully Qualified Domain Name for the image.

        :return: image Fully Qualified Domain Name
        """
        if not self.__fqdn:
            self.__fqdn = utils.generate_fqdn_image(
                self.registry, self.namespace, self.name, self.tag
            )
        return self.__fqdn

    @property
    def dockerfile(self):
        """
        Returns the Dockerfile for the image.

        :return: Dockerfile for the image
        """
        if not self.__dockerfile:
            self.__dockerfile = utils.image_to_dockerfile(self.name)
        return self.__dockerfile

    @classmethod
    def from_context_obj(cls, ctx_obj):
        """
        Creates an instance of Image from a given context.

        :param ctx_obj: Click context object
        :return: An instance of Image
        """
        if ctx_obj is None:
            return None

        return cls(
            name=ctx_obj.get("build_container_image"),
            tag=ctx_obj.get("build_container_tag"),
            registry=ctx_obj.get("registry"),
        )


@dataclass
class BuildOptions:
    """
    A class to encapsulate all the build options needed to create Docker image.
    """

    def __init__(
        self,
        image: Image,
        container_context,
        build_contexts=None,
        build_args=None,
        use_cache=False,
    ):
        """
        Constructs all the necessary attributes for the build options.

        :param image: image details as an instance of Image
        :param container_context: Context for the build
        :param build_contexts: Build contexts to add to build
        :param build_args: Arguments to pass to build
        :param use_cache: Boolean indicating if cache should be used
        """
        self.image = image
        self.container_context = container_context
        self.build_contexts = [ctx for ctx in build_contexts if ctx] if build_contexts else []
        self.build_args = [arg for arg in build_args if arg] if build_args else []
        self.use_cache = use_cache

    @classmethod
    def from_context_obj(cls, ctx_obj):
        """
        Creates an instance of BuildOptions from a given context.

        :param ctx_obj: Click context object
        :return: An instance of BuildOptions
        """
        if ctx_obj is None:
            return None

        return cls(
            image=Image.from_context_obj(ctx_obj),
            container_context=ctx_obj.get("container_context"),
            build_contexts=ctx_obj.get("build_contexts"),
            build_args=ctx_obj.get("build_args"),
            use_cache=ctx_obj.get("use_cache"),
        )


def build(options: BuildOptions, runner: Callable, logger: Logger) -> int:
    """
    Builds a image based on given build options and runner function.

    :param options: Build options as an instance of BuildOptions
    :param runner: Callable that runs the Docker commands
    :param logger: Logger instance
    :return: A return code representing the success or failure of the build
    """
    cmd = ["build", "--network=host"]

    for arg in options.build_args:
        cmd += ["--build-arg", arg]

    for build_ctx in options.build_contexts:
        cmd += ["--build-context", build_ctx]

    cmd += [
        "-f",
        options.image.dockerfile,
        "-t",
        options.image.local,
        options.container_context or ".",
    ]

    if options.use_cache:
        runner(["pull", options.image.cache_fqdn])
        cmd.extend(["--cache-from", options.image.cache_fqdn])

    ret = runner(cmd)

    if ret != 0:
        logger.error("Failed to build image: %s", options.image)
        return ret

    if options.use_cache:
        runner(["tag", options.image.name, options.image.cache_fqdn])
        runner(["push", options.image.cache_fqdn])

    return 0
