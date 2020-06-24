#!/usr/bin/env python3
import atexit
import logging
import shutil
from functools import partial
from pathlib import Path

import coloredlogs
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import Config
from .git import mirror_repository, repository_exists


def create_scheduler(config: Config):
    scheduler = BlockingScheduler(executors={"default": ThreadPoolExecutor()})
    for repository in config.repositories:
        scheduler.add_job(
            partial(mirror_repository, repository, config),
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
    config = Config.from_file(Path() / "repositories.toml")
    config.clone_root.mkdir(exist_ok=True)

    active_repo_dirs = {repo.directory_name for repo in config.repositories}

    for repo_dir in config.clone_root.iterdir():
        if repo_dir.is_dir() and repo_dir.name not in active_repo_dirs:
            logging.warn("Cleaning up %s", repo_dir)
            shutil.rmtree(config.clone_root / repo_dir)

    all_repositories_exist = True
    for repository in config.repositories:
        for repository_url in [
            repository.expanded_source,
            repository.expanded_destination,
        ]:
            logging.info("Checking %s exists", repository_url)
            if not repository_exists(repository_url):
                all_repositories_exist = False

    if not all_repositories_exist:
        logging.error("Some repositories do not exist.")
        exit(1)

    logging.info("All repositories exist!")

    scheduler = create_scheduler(config)
    atexit.register(scheduler.shutdown)
    scheduler.start()


if __name__ == "__main__":
    main()
