#!/usr/bin/env bash

set -e

PATH=env/bin:${PATH}

set -x

black --check git_mirror/
flake8 git_mirror/
isort -c -rc git_mirror/
mypy git_mirror/
