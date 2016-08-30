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

Use Skipper as your primary tool for your daily development tasks:
* Use `skipper build` to build the Dockerfile(s) of your repository. All the images will be automatically tagged with the *COMMIT_ID*.
* Use `skipper push` to publish your containers.
* Use `skipper make` to execute makefile targets inside a container.
* Use `skipper run` to run arbitrary commands inside a container.

### Global CLI Flags

```
-q, --quiet                   Silence the output
--nested / --no-nested        Run inside a build contanier
--registry                    URL of the docker registry
--build-container-image       Image to use as build container
--build-container-tag         Tag of the build container
--help                        Show this message and exit.
```

### Build Command CLI Flags

```
Positional arguments:
image       The image to build
```

### Push Command CLI Flags

```
Positional arguments:
image       The image to push
```
### Make Command CLI Flags

```
Positional arguments:
target          The target to execute

Optional arguments:
-f, --file      Path to the makefile
-e, --env       Environement variables to pass to the build container
```

### Run Command CLI Flags

```
Positional arguments:
target          The target to execute

Optional arguments:
-e, --env       Environement variables to pass to the build container
```
