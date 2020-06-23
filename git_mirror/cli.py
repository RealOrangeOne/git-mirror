#!/usr/bin/env python3
import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import List

import toml
from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass
class Repo:
    source: str
    destination: str

    @property
    def directory_name(self) -> str:
        return hashlib.sha1(
            (self.expanded_source + self.expanded_destination).encode()
        ).hexdigest()

    def display(self) -> str:
        return f"{self.source} -> {self.destination}"

    @property
    def expanded_source(self):
        return os.path.expandvars(self.source)

    @property
    def expanded_destination(self):
        return os.path.expandvars(self.destination)


@dataclass
class Config:
    repo: List[Repo] = Field(default_factory=list)
    clone_root: Path = Path(__file__).resolve().parent / "repos"

    @classmethod
    def from_file(cls, file: Path) -> "Config":
        return cls(**toml.loads(file.read_text()))

    @property
    def repos(self) -> List[Repo]:
        """
        Stupid TOML
        """
        return self.repo

    def directory_for_repo(self, repo: Repo) -> Path:
        return self.clone_root / repo.directory_name


def git(command: List[str], cwd: Path) -> str:
    return subprocess.check_output(["git"] + command, cwd=cwd).decode()


def get_repo(config: Config, repo: Repo):
    directory = config.directory_for_repo(repo)
    if directory.exists():
        git(["fetch", "--quiet"], cwd=directory)
    else:
        git(
            ["clone", "--quiet", "--bare", repo.expanded_source, str(directory)],
            cwd=config.clone_root,
        )


def push_repo(config: Config, repo: Repo):
    directory = config.directory_for_repo(repo)
    assert directory.exists()
    git(["push", "--mirror", "--quiet", repo.expanded_destination], cwd=directory)


def git_gc(directory: Path):
    git(["gc", "--auto", "--quiet"], cwd=directory)


def main():
    config = Config.from_file(Path() / "repos.toml")
    config.clone_root.mkdir(exist_ok=True)
    for repo in config.repos:
        print("Updating", repo.display())
        repo_dir = config.clone_root / repo.directory_name
        get_repo(config, repo)
        push_repo(config, repo)
        git_gc(repo_dir)

    active_repo_dirs = {repo.directory_name for repo in config.repos}
    all_repos = {d.name for d in config.clone_root.iterdir() if d.is_dir()}
    defunct_repos = all_repos - active_repo_dirs
    for defunct_repo in defunct_repos:
        print("Cleaning up", defunct_repo)
        shutil.rmtree(config.clone_root / defunct_repo)


if __name__ == "__main__":
    main()
