import subprocess
from pathlib import Path
from typing import List

from .config import Config, Repository


def git(command: List[str], cwd: Path) -> str:
    return subprocess.check_output(
        ["git"] + command, cwd=cwd, stderr=subprocess.DEVNULL
    ).decode()


def get_repo(config: Config, repository: Repository):
    directory = config.directory_for_repository(repository)
    if directory.exists():
        git(["fetch", "--quiet", "--prune", "--prune-tags"], cwd=directory)
    else:
        git(
            [
                "clone",
                "--quiet",
                "--mirror",
                repository.expanded_source,
                str(directory),
            ],
            cwd=config.clone_root,
        )


def push_repo(config: Config, repository: Repository):
    directory = config.directory_for_repository(repository)
    assert directory.exists()
    git(
        ["push", "--mirror", "--quiet", "--prune", repository.expanded_destination],
        cwd=directory,
    )


def git_gc(directory: Path):
    git(["gc", "--auto", "--quiet"], cwd=directory)


def mirror_repository(repository: Repository, config: Config):
    get_repo(config, repository)
    push_repo(config, repository)
    git_gc(config.directory_for_repository(repository))


def repository_exists(url: str) -> bool:
    try:
        git(["ls-remote", "--heads", "--quiet", url], cwd=Path.cwd())
        return True
    except subprocess.CalledProcessError:
        return False
