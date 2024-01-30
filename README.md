# Skipper

## Easily dockerize your Git repository

[![Build Status](https://github.com/Stratoscale/skipper/workflows/build/badge.svg?branch=upstream)](https://github.com/Stratoscale/skipper/actions) [![Release Status](https://github.com/Stratoscale/skipper/workflows/Releases/badge.svg)](https://github.com/Stratoscale/skipper/actions) [![PyPI - Version](https://img.shields.io/pypi/v/strato-skipper?logo=pypi&label=pypi%20package&color=2334D058&cacheSeconds=10)](https://pypi.org/project/strato-skipper)

## Introduction

Use Skipper to build & test your project in an isolated environment, using Docker containers with pre-defined sane configuration.
Skipper allows you to execute makefile targets inside a container (or just run arbitrary commands). You can also use Skipper to build your development and production containers.

## Installation

It is recommended to install Skipper directly from PyPi:

```shell
sudo pip install strato-skipper
``` 

You can also install Skipper from source:

``` shell
git clone http://github.com/Stratoscale/skipper
sudo make install
```

Configure bash completion for skipper by sourcing the completion script in your ~/.bashrc file:

``` bash
echo 'source <(skipper completion)' >>~/.bashrc
```

## Python3 Environment

Skipper supports building and running in Python3 environment
Set your locale to UTF-8:

```shell
export LC_ALL="en_US.UTF-8"
export LANG="en_US.UTF-8"
```

## Note for Linux Users with Docker

If you run on Linux and use Docker without sudo, Skipper will create a dedicated user inside the build container with both root and docker groups. Commands are executed on behalf of this user.

To preserve the environment (e.g., PATH), Skipper uses the `su` command with the `-m` flag. However, on Debian distros, even with the `-m` flag specified, the PATH variable may be reset. As a workaround, Skipper attempts to use `sudo -sE` (if installed) as an alternative to maintain the environment.

If you prefer to use sudo, please install it in the build container. Additionally, it is required to disable `env_reset` with `secure_path` in `/etc/sudoers` Deafults.

**Note:** This information is crucial for a seamless experience when using Skipper with Docker on Linux.


## Usage

Skipper can serve as your primary tool for your daily development tasks:

* Use `skipper build` to build the images defined by the Dockerfiles in your repository. All the images will be automatically tagged with the *COMMIT_ID*.
* Use `skipper push` to publish your images.
* Use `skipper images` to list your images.
* Use `skipper rmi` to delete your images.
* Use `skipper make` to execute makefile targets inside a container.
* Use `skipper run` to run arbitrary commands inside a container.
* Use `skipper shell` to get an interactive shell inside a container.

### Global Options

```shell
  -v, --verbose                 Increase verbosity
  --registry                    URL of the docker registry
  --build-container-image       Image to use as build container
  --build-container-tag         Tag of the build container
  --build-container-net         Network to connect the build container (default: net=host)
  --env-file                    Environment variables file/s to pass to the container
  --build-arg                   Set build-time variables for the container
  --build-context               Additional build contexts when running the build command, give them a name, and then access them inside a Dockerfile
  --help                        Show this message and exit.
```

### [Build context explained](https://www.docker.com/blog/dockerfiles-now-support-multiple-build-contexts/)

Skipper allows you to add additional build contexts when running the build command, give them a name, and then access them inside a Dockerfile.
The build context can be one of the following:

* Local directory – e.g. `--build-context project2=../path/to/project2/src`
* Git repository – e.g. `--build-context qemu-src=https://github.com/qemu/qemu.git`
* HTTP URL to a tarball – e.g. `--build-context src=https://example.org/releases/src.tar`
* Docker image – Define with a `docker-image://` prefix, e.g. `--build-context alpine=docker-image://alpine:3.15`

On the Dockerfile side, you can reference the build context on all commands that accept the “from” parameter. Here’s how that might look:

```dockerfile
FROM [name]
COPY --from=[name] ...
RUN --mount=from=[name] …
```

### Build

As a convention, skipper infers the docker images from the Dockerfiles in the top directory of your repository. For example, assuming that there are 3 Dockerfile in the top directory of the repository:

```
Dockerfile.service1
Dockerfile.service2
Dockerfile.development
```

To build the image that corresponeds to `Dockerfile.service1`, run:

```shell
skipper build service1
```

In the same way you can build the image corresponded to `Dockerfile.development`:

```shell
skipper build development
```

You can also build mutliple images with single command:

```shell
skipper build development service2
```

A context path can be added to the build command, The build’s context is the files at a specified location PATH, the default is current directory:

```shell
skipper buid service1 --container-context /path/to/context/dir
```

If no image is specifed skipper will build all detected images:

```shell
skipper build
```

If you don't want to store all the Dockerfiles under the top directory of the project, you can specify the project's containers in skipper's config file (see below).

### Push

Once you've built the images of your repositories as described above. You can publish them by pushing them to the registry.
To push the `service1` image, run:

```shell
skipper --registry some-registry push service1
```

Note that the registry in this command must be the same registry used while building the image.

### Images

To list local images of your repository, run:

```shell
skipper images
```

In order to also list also images that were pushed to the registry, run:

```shell
skipper --registry some-registry images -r
```

### Rmi

To delete an image of your repository, run:

```shell
skipper rmi service1 <tag>
```

In order to delete the image from the registry, run:

```shell
skipper --registry some-registry rmi -r service1 <tag>
```

### Make

You can execute a Makefile target inside a container. This is good for keeping the development in an isolated environment, without installing development tools on the host. Once a development container is defined and built, it can be shared among the team member, assuring all of them use exactly thg same development environment.
Assuming your project has a Makefile with a `tests` target, you can run:

```shell
skipper --registry some-registry --build-container-image development --build-container-tag latest \
make tests
```

If your Makefile is not standard (i.e. `Makefile.arm32`) you can pass it to the make command:

```shell
skipper --registry some-registry --build-container-image development --build-container-tag latest \
make -f Makefile.arm32 tests
```

### Run

You can also run arbitrary commands inside your containers.

```shell
skipper --registry some-registry --build-container-image development --build-container-tag latest \
run gcc myprog.c -o myprog 
```

### Shell

You can get a shell inside your containers.

```shell
skipper --registry some-registry --build-container-image development --build-container-tag latest \
shell
```

## Configuration File

Skipper allows you to define commonly used parameters in a configuration file `skipper.yaml` at the top directory of your repositry.

```yaml
registry: some-registry 
build-container-image: development
build-container-tag: latest
container-context: /path/to/context/dir

build-arg:
  - VAR1=value1
  - VAR2=value2

build-context:
  - context1=/path/to/context/dir # Local directory
  - qemu-src=https://github.com/qemu/qemu.git # Remote git repository
  - src=https://example.org/releases/src.tar # Remote tar file
  - alpine=docker-image://alpine:3.15 # Remote docker image

make: 
    makefile: Makefile.arm32
containers:
    service1: path/to/service1/dockerfile
    service2: path/to/service2/dockerfile
env:
    VAR: value
env_file: path/to/env_file.env
```

```yaml
# Use the git revision as the build container tag
# Allows to use the same build container unless the git revision changes
# This is useful when using a CI system that caches the build container
# Remember to commit if you changing the build container
build-container-tag: 'git:revision'
```

Using the above configuration file, we now can run a simplified version of the make command described above:

```shell
skipper make tests
```

### Published ports

For `shell`, `run` & `make` commands:  
By default, when you run skipper on a linux machine it will use the host network and no mapping required.  
For macos and windows machines where the host network is unsupported or for a custom network, you can publish a port and make it available to services outside of the container using the --publish or -p flag.

````shell
skipper make -p 123:123 tests
skipper make -p 123-130:123-130 tests
````

### Environment variables

For `shell`, `run` & `make` commands:
You can use `-e` in order to pass environment variables to the container.

````shell
skipper make -e regex=test1 tests
````

Your configuration file can contain environment variables, Skipper will set the specified environment variables in the container.

````yaml
env:
    VAR: value
````

You can add an environment variables file (or multiple files) using `--env-file`.
This file should use the syntax <key>=value (which sets the variable to the given value) or <key>
(which takes the value from the local environment), and # for comments.
The variables defined in this file will be exported to the container.
Such file can look like this:

````shell
$ cat env_file.env
# This is a comment
KEY1=value1
KEY2=value2
KEY3    
````

Skipper configuration file can include the environment variables file:

````yaml
env_file: 
    - /path/to/env_file1.env
    - /path/to/env_file2.env
````

### Variable substitution

Skipper uses the variable values from the shell environment in which skipper is run.
It’s possible to use environment variables in your shell to populate values
For example, suppose the shell contains EXTERNAL_PORT=5000 and you supply this configuration:

````yaml
env:
    EXTERNAL_PORT: $EXTERNAL_PORT
````

When you run Skipper command with this configuration, Skipper looks for the EXTERNAL_PORT environment variable in the shell and substitutes its value in.In this example, Skipper resolves the `$EXTERNAL_PORT` to "5000" and will set EXTERNAL_PORT=5000 environment in the container.

If an environment variable is not set, Skipper substitutes with an empty string.

Both `$VARIABLE` and `${VARIABLE}` syntax are supported. Extended shell-style features, such as `${VARIABLE-default}` and `${VARIABLE/foo/bar}`, are not supported.

You can use a `$$` (double-dollar sign) when your configuration needs a literal dollar sign. This also prevents Skipper from interpolating a value, so a `$$` allows you to refer to environment variables that you don’t want processed by Skipper.

````yaml
env:
    VAR: $$VAR_NOT_INTERPOLATED
````

### Shell Interpolation

Skipper supports evaluating shell commands inside its configuration file using `$(command)` notation.
e.g.

```yaml
env:
    VAR: $(expr ${MY_NUMBER:-5} + 5)
volumes:
    - $(which myprogram):/myprogram
```

### Volumes

Skipper can bind-mount a host directory into the container.
you can add volumes in the configuration file:

````yaml
volumes:
  - /tmp:/tmp:rw
  - ${HOME}/.netrc:/root/.netrc
  - ${HOME}/.gocache:/tmp/.gocache
````

### Workdir

Skipper default to the the project directory as the working directory for the `run`, `make` and `shell` commands,
you can override the workdir by specifying it in the configuration file:

````yaml
workdir: /path/to/workdir
````

### Workspace

Skipper default to the the project base directory (e.g. /path/to/project/../) as the workspace for the `run`, `make` and `shell` commands,
Note that the workspace directory is mounted by default.
you can override the workspace directory by specifying it in the configuration file

````yaml
workdir: $PWD
````

### Skipper environment variables

Skipper sets environemnt variables to inform the user about the underline system:
CONTAINER_RUNTIME_COMMAND - The container conmmand used to run the skipper container. podman/docker
