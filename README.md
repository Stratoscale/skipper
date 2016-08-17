# Introduction

Skipper - Easily dockerize your Git repository

Define your workflow in the `skipper.yaml` and use skipper to your Continuous Delivery service to create containers for each commit, test them and push them to your registry only when tests passes.

* Use `skipper build` to build your Dockerfile(s) of your repository. If your repository has local changes the containers will only be tagged as *latest*, otherwise the containers will be tagged as *latest*, *COMMIT_ID* & *BRANCH_NAME*. Now your Git commit tree is reproduced in your local docker repository.
* Use `skipper run` to run commands inside a container
* Use `captain make` to execute makefile targets inside a container

From the other side, you can now pull the feature branch you want to test, or create distribution channels (such as 'alpha', 'beta', 'stable') using git tags that are propagated to container tags.

## Installation

To install Skipper, run:
```
git clone http://github.com/Stratoscale/skipper
pip install .
```

## skipper.yml Format

TBD

## Global CLI Flags

```
-v, --verbose: Increase verbosity
-h, --help: help for skipper
```

## Docker Tags Lifecycle

The following is the workflow of tagging Docker images according to git state.

- If you're in non-git repository, skipper will tag the built images with `latest`.
- If you're in dirty-git repository, skipper will tag the built images with `latest`.
- If you're in pristine-git repository, skipper will tag the built images with `latest`, `commit-id`, `branch-name`, `tag-name`. A maximum of one tag per commit id is supported.

## Roadmap
TBD
