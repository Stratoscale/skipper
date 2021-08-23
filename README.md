[![Actions Status](https://github.com/Stratoscale/skipper/workflows/build/badge.svg)](https://github.com/Stratoscale/skipper/actions)
# Skipper

## Introduction

Use Skipper to build & test your project in an isolated environment, using Docker containers with pre-defined sane configuration.
Skipper allows you to execute makefile targets inside a container (or just run arbitrary commands). You can also use Skipper to build your development and production containers.

## Installation

It is recommended to install Skipper directly from PyPi:
```bash
sudo pip install strato-skipper
```

You can also install Skipper from source:
``` bash 
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
```bash
export LC_ALL="en_US.UTF-8"
export LANG="en_US.UTF-8"
```
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
```bash
  -v, --verbose                 Increase verbosity
  --registry                    URL of the docker registry
  --build-container-image       Image to use as build container
  --build-container-tag         Tag of the build container
  --build-container-net         Network to connect the build container (default: net=host)
  --env-file                    Environment variables file/s to pass to the container
  --help                        Show this message and exit.
```

### Build
As a convention, skipper infers the docker images from the Dockerfiles in the top directory of your repository. For example, assuming that there are 3 Dockerfile in the top directory of the repository:
```
Dockerfile.service1
Dockerfile.service2
Dockerfile.development
```

To build the image that corresponeds to `Dockerfile.service1`, run:
```bash
skipper build service1
```

In the same way you can build the image corresponded to `Dockerfile.development`:
```bash
skipper build development
```

You can also build mutliple images with single command:
```bash
skipper build development service2
```

A context path can be added to the build command, The build’s context is the files at a specified location PATH, the default is current directory:
```bash
skipper buid service1 --container-context /path/to/context/dir
```

If no image is specifed skipper will build all detected images:
```bash
skipper build
```

If you don't want to store all the Dockerfiles under the top directory of the project, you can specify the project's containers in skipper's config file (see below).

### Push
Once you've built the images of your repositories as described above. You can publish them by pushing them to the registry.
To push the `service1` image, run:
```bash
skipper --registry some-registry push service1
```
Note that the registry in this command must be the same registry used while building the image.

### Images
To list local images of your repository, run:
```bash
skipper images
```

In order to also list also images that were pushed to the registry, run:
```bash
skipper --registry some-registry images -r
```

### Rmi
To delete an image of your repository, run:
```bash
skipper rmi service1 <tag>
```

In order to delete the image from the registry, run:
```bash
skipper --registry some-registry rmi -r service1 <tag>
```

### Make
You can execute a Makefile target inside a container. This is good for keeping the development in an isolated environment, without installing development tools on the host. Once a development container is defined and built, it can be shared among the team member, assuring all of them use exactly thg same development environment.
Assuming your project has a Makefile with a `tests` target, you can run:
```bash
skipper --registry some-registry --build-container-image development --build-container-tag latest \
make tests
```

If your Makefile is not standard (i.e. `Makefile.arm32`) you can pass it to the make command:
```bash
skipper --registry some-registry --build-container-image development --build-container-tag latest \
make -f Makefile.arm32 tests
```

### Run
You can also run arbitrary commands inside your containers. 
```bash
skipper --registry some-registry --build-container-image development --build-container-tag latest \
run gcc myprog.c -o myprog 
```

### Shell
You can get a shell inside your containers. 
```bash
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

make: 
    makefile: Makefile.arm32
containers:
    service1: path/to/service1/dockerfile
    service2: path/to/service2/dockerfile
env:
    VAR: value
env_file: path/to/env_file.env
```

Using the above configuration file, we now can run a simplified version of the make command described above:
```bash
skipper make tests
```

### Published ports
For `shell`, `run` & `make` commands:  
By default, when you run skipper on a linux machine it will use the host network and no mapping required.  
For macos and windows machines where the host network is unsupported or for a custom network, you can publish a port and make it available to services outside of the container using the --publish or -p flag. 

````
skipper make -p 123:123 tests
skipper make -p 123-130:123-130 tests
````


### Environment variables:
For `shell`, `run` & `make` commands:
You can use `-e` in order to pass environment variables to the container.
````
skipper make -e regex=test1 tests
````

Your configuration file can contain environment variables, Skipper will set the specified environment variables in the container.
````
env:
    VAR: value
````

You can add an environment variables file (or multiple files) using `--env-file`.
This file should use the syntax <key>=value (which sets the variable to the given value) or <key> 
(which takes the value from the local environment), and # for comments.
The variables defined in this file will be exported to the container.
Such file can look like this:

````
$ cat env_file.env
# This is a comment
KEY1=value1
KEY2=value2
KEY3    
````

Skipper configuration file can include the environment variables file:
````
env_file: 
    - /path/to/env_file1.env
    - /path/to/env_file2.env
````


### Variable substitution:
Skipper uses the variable values from the shell environment in which skipper is run.
It’s possible to use environment variables in your shell to populate values
For example, suppose the shell contains EXTERNAL_PORT=5000 and you supply this configuration:
````
env:
    EXTERNAL_PORT: $EXTERNAL_PORT
````
When you run Skipper command with this configuration, Skipper looks for the EXTERNAL_PORT environment variable in the shell and substitutes its value in.In this example, Skipper resolves the $EXTERNAL_PORT to "5000" and will set EXTERNAL_PORT=5000 environment in the container.

If an environment variable is not set, Skipper substitutes with an empty string.

Both $VARIABLE and ${VARIABLE} syntax are supported. Extended shell-style features, such as ${VARIABLE-default} and ${VARIABLE/foo/bar}, are not supported.

You can use a $$ (double-dollar sign) when your configuration needs a literal dollar sign. This also prevents Skipper from interpolating a value, so a $$ allows you to refer to environment variables that you don’t want processed by Skipper.
````
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


### Volumes:
Skipper can bind-mount a host directory into the container.
you can add volumes in the configuration file:
````
volumes:
  - /tmp:/tmp:rw
  - ${HOME}/.netrc:/root/.netrc
  - ${HOME}/.gocache:/tmp/.gocache
````

### Workdir:
Skipper default to the the project directory as the working directory for the `run`, `make` and `shell` commands,
you can override the workdir by specifying it in the configuration file:
````
workdir: /path/to/workdir
````

### Workspace:
Skipper default to the the project base directory (e.g. /path/to/project/../) as the workspace for the `run`, `make` and `shell` commands,
Note that the workspace directory is mounted by default.
you can override the workspace directory by specifying it in the configuration file
````
workdir: $PWD
````

### Skipper environment variables
Skipper sets environemnt variables to inform the user about the underline system:
CONTAINER_RUNTIME_COMMAND - The container conmmand used to run the skipper container. podman/docker