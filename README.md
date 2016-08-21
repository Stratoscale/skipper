# Skipper

## Introduction

Use Skipper to build & test your project in an isolated environment using Docker containers with pre-defined sane configuration.
Skipper allows you to execute makefile targets inside a container (or just run arbitrary commands). You can also use Skipper to build your development and production containers.

## Installation

To install Skipper, run:
``` bash 
git clone http://github.com/Stratoscale/skipper
python setup.py install
```

## Usage

Use Skipper as your primary tool for your daily development tasks:
* Use `skipper build` to build your Dockerfile(s) of your repository. If your repository has local changes the containers will only be tagged as *latest*, otherwise the containers will be tagged as *latest*, *COMMIT_ID* & *BRANCH_NAME*. Now your Git commit tree is reproduced in your local docker repository.
* Use `skipper make` to execute makefile targets inside a container.
* Use `skipper run` to run arbitrary commands inside a container.

### Global CLI Flags

```
--registry      url of the docker registry
--image         docker image to use for running commands
--tag           tag of the docker image
-q, --quiet     silence the output
-h, --help      show help
```

### Build Command CLI Flags

```
positional argument:
target          the target to execute

optional arguments:
-f, --file      path to the dockerfile
--image         docker image to use (for build / run commands)
--tag           tag of the docker image
```

### Make Command CLI Flags

```
-f, --file      path to the makefile
```

### Run Command CLI Flags

```
positional argument:
command         the command to run
```
