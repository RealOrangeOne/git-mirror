#!/usr/bin/env python3
import atexit
import hashlib
import logging
import os
import shutil
import subprocess
import urllib.request
from functools import partial
from pathlib import Path
from typing import List, Optional

import coloredlogs
import toml
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel, HttpUrl, ValidationError


class Repository(BaseModel):
    source: str
    destination: str
    interval: int = 15

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

    def do_update(self, config: "Config"):
        get_repo(config, self)
        push_repo(config, self)
        git_gc(config.directory_for_repository(self))


class Config(BaseModel):
    repository: List[Repository]
    clone_root: Path = Path(__file__).resolve().parent / "repos"
    heartbeat: Optional[HttpUrl] = None

    @classmethod
    def from_file(cls, file: Path) -> "Config":
        try:
            return cls.parse_obj(toml.loads(file.read_text()))
        except ValidationError as e:
            logging.error("%s", e)
            exit(1)

    @property
    def repositories(self) -> List[Repository]:
        """
        Stupid TOML
        """
        return self.repository

    def directory_for_repository(self, repository: Repository) -> Path:
        return self.clone_root / repository.directory_name

    def send_heartbeat(self):
        if self.heartbeat:
            with urllib.request.urlopen(str(self.heartbeat)) as response:
                response.read()


def git(command: List[str], cwd: Path) -> str:
    return subprocess.check_output(["git"] + command, cwd=cwd).decode()


def get_repo(config: Config, repository: Repository):
    directory = config.directory_for_repository(repository)
    if directory.exists():
        git(["fetch", "--quiet"], cwd=directory)
    else:
        git(
            ["clone", "--quiet", "--bare", repository.expanded_source, str(directory)],
            cwd=config.clone_root,
        )


def push_repo(config: Config, repository: Repository):
    directory = config.directory_for_repository(repository)
    assert directory.exists()
    git(["push", "--mirror", "--quiet", repository.expanded_destination], cwd=directory)


def git_gc(directory: Path):
    git(["gc", "--auto", "--quiet"], cwd=directory)


def create_scheduler(config: Config):
    scheduler = BlockingScheduler(executors={"default": ThreadPoolExecutor()})
    for repository in config.repositories:
        scheduler.add_job(
            partial(repository.do_update, config),
            "interval",
            minutes=repository.interval,
            name=repository.display(),
        )
    if config.heartbeat:
        scheduler.add_job(
            config.send_heartbeat,
            "interval",
            minutes=min(repository.interval for repository in config.repositories),
        )

    # Make sure jobs also execute at startup
    for job in scheduler.get_jobs():
        if isinstance(job.trigger, IntervalTrigger):
            scheduler.add_job(job.func, name=job.name)

    return scheduler


def main():
    coloredlogs.install(
        level=logging.INFO, fmt="%(asctime)s %(levelname)s %(message)s",
    )
    config = Config.from_file(Path() / "repos.toml")
    config.clone_root.mkdir(exist_ok=True)

    active_repo_dirs = {repo.directory_name for repo in config.repositories}

    for repo_dir in config.clone_root.iterdir():
        if repo_dir.is_dir() and repo_dir.name not in active_repo_dirs:
            logging.warn("Cleaning up %s", repo_dir)
            shutil.rmtree(config.clone_root / repo_dir)

    scheduler = create_scheduler(config)
    atexit.register(scheduler.shutdown)
    scheduler.start()


if __name__ == "__main__":
    main()
