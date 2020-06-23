#!/usr/bin/env python3
import hashlib
import os
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


def main():
    repos_dir = Path() / "repos"
    repos = get_repos()
    print(f"Found {len(repos)} repos")
    repos_dir.mkdir()
    for repo in repos:
        print(repos_dir / repo.directory_name)


if __name__ == "__main__":
    main()
