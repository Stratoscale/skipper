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

## Usage

Skipper can serve as your primary tool for your daily development tasks:
* Use `skipper build` to build the images defined by the Dockerfiles in your repository. All the images will be automatically tagged with the *COMMIT_ID*.
* Use `skipper push` to publish your images.
* Use `skipper images` to list your images.
* Use `skipper rmi` to delete your images.
* Use `skipper make` to execute makefile targets inside a container.
* Use `skipper run` to run arbitrary commands inside a container.

### Global Options
```bash
  -v, --verbose                 Increase verbosity
  --registry                    URL of the docker registry
  --build-container-image       Image to use as build container
  --build-container-tag         Tag of the build container
  --help                        Show this message and exit.
```
Note that registry is mandatory parameter, as it is used to indentify the images.

### Build
Skipper infers the docker images from the Dockerfiles in the top directory of your repository. For example, assuming that there are 2 Dockerfile in the top directory of the repository:
```
Dockerfile.production
Dockerfile.development
```

To build the image that corresponeds to `Dockerfile.production`, run:
```bash
skipper --registry some-registry build production
```

In the same way you can build the image corresponded to `Dockerfile.development`:
```bash
skipper --registry some-registry build development
```

You can also build mutliple images with single command:
```bash
skipper --registry some-registry build development production
```

If no image is specifed skipper will build all detected images:
```bash
skipper --registry some-registry build
```

### Push
Once you've built the images of your repositories as described above. You can publish them by pushing them to the registry.
To push the `production` image, run:
```bash
skipper --registry some-registry push production
```
Note that the registry in this command must be the same registry used while building the image.

### Images
To list images of your repository, run:
```bash
skipper --registry some-registry images
```

In order to also list also images that were pushed to the registry, run:
```bash
skipper --registry some-registry images -r
```

### Rmi
To delete an image of your repository, run:
```bash
skipper --registry some-registry rmi production <tag>
```

In order to delete the image from the registry, run:
```bash
skipper --registry some-registry rmi -r production <tag>
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

make: 
    makefile: Makefile.arm32
env:
    VAR: value
```

Using the above configuration file, we now can run a simplified version of the make command described above:
```bash
skipper make tests
```

###Environment variables:
For `shell`, `run` & `make` commands:
You can use `-e` in order to pass environment variables to the container.
````
skipper make -e regex=test1 tests
````

Your configuration file can contain environment variables, Skipper will set the specified environment variables in the container.
````
env:
    VAR: value
```


###Variable substitution:
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


