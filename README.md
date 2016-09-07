# Skipper

## Introduction

Use Skipper to build & test your project in an isolated environment using Docker containers with pre-defined sane configuration.
Skipper allows you to execute makefile targets inside a container (or just run arbitrary commands). You can also use Skipper to build your development and production containers.

## Installation

To install Skipper, run:
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
Skipper infers the docker images from the Dockerfiles in the top directory of your repository. For example, assume there are 2 Dockerfile in the top directory of the repository:
```
Dockerfile.production
Dockerfile.development
```

To build the image corresponeded to `Dockerfile.production`, run:
```bash
skipper --registry some-registry build production
```

In the same way you can build the image corresponded to `Dockerfile.development`:
```bash
skipper --registry some-registry build development
```

### Push
Once you've built the images of you your repositories as described above. You can publish them by pushing them to the registry.
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

In order to list also images that were pushed to the registry, run:
```bash
skipper --registry some-registry images -r
```

### Rmi
To delete image of your repository, run:
```bash
skipper --registry some-registry rmi production <tag>
```

In order to delete image from the registry, run:
```bash
skipper --registry some-registry rmi -r production <tag>
```

### Make
You can execute Makefile target inside a container. This is good for keeping the development in an isolated environment, without installing development tools on the host. Once a development container is defined and built, it can be shared among the team member, assuring all of them use exactly thg same development environment.
Assuming your project has a Makefile with `tests` target, you can run:
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

## Configuration File
Skipper allows you to define commonly used parameters in a configuration file `skipper.yaml` at the top directory of your repositry.
```yaml
registry: some-registry 
build-container-image: development
build-container-tag: latest

make: 
    makefile: Makefile.arm32
```

Using the above configuration file, we now can run a simplified version of the make command described above:
```bash
skipper make tests
```
