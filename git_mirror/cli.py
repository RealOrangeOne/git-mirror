#!/usr/bin/env python3
import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import toml


@dataclass
class Repo:
    source: str
    destination: str

    @classmethod
    def from_config(cls, config: dict):
        return cls(
            source=os.path.expandvars(config["source"]),
            destination=os.path.expandvars(config["destination"]),
        )

    @property
    def directory_name(self) -> str:
        return hashlib.sha1((self.source + self.destination).encode()).hexdigest()


def get_repos():
    config_file = Path() / "repos.toml"
    config = toml.loads(config_file.read_text())

    repos = []
    for repo_config in config["repo"]:
        repos.append(Repo.from_config(repo_config))
    return repos


def git(*command: str, cwd=None) -> str:
    git_command = ["git", *command]
    print("Running", git_command, "for", cwd)
    return subprocess.check_output(git_command, cwd=cwd or Path(),).decode()


def get_repo(repo: Repo, directory: Path):
    if directory.exists():
        git("fetch", "--quiet", cwd=directory)
    else:
        git("clone", "--quiet", "--bare", repo.source, str(directory))


def push_repo(repo: Repo, directory: Path):
    assert directory.exists()
    git("push", "--mirror", "--quiet", repo.destination, cwd=directory)


def main():
    repos_dir = Path().resolve() / "repos"
    repos = get_repos()
    print(f"Found {len(repos)} repos")
    repos_dir.mkdir(exist_ok=True)
    for repo in repos:
        repo_dir = repos_dir / repo.directory_name
        get_repo(repo, repo_dir)
        push_repo(repo, repo_dir)


if __name__ == "__main__":
    main()
