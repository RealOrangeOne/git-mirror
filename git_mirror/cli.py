#!/usr/bin/env python3
import logging
import shutil
import time
from pathlib import Path

import coloredlogs

from .config import Config
from .git import mirror_repository, repository_exists


def do_mirror(config: Config):
    for repository in config.repositories:
        logging.info("Mirroring %s", repository.display())
        mirror_repository(repository, config)

    if config.heartbeat:
        logging.info("Sending heartbeat")
        config.send_heartbeat()


def check_repositories(config: Config):
    all_repositories_exist = True
    for repository in config.repositories:
        for repository_url in [
            repository.expanded_source,
            repository.expanded_destination,
        ]:
            if not repository_exists(repository_url):
                logging.error("Unable to find %s", repository_url)
                all_repositories_exist = False

    if not all_repositories_exist:
        logging.error("Aborting - Some repositories do not exist.")
        exit(1)


def prune_repositories(config: Config):
    active_repo_dirs = {repo.directory_name for repo in config.repositories}

    for repo_dir in config.clone_root.iterdir():
        if repo_dir.is_dir() and repo_dir.name not in active_repo_dirs:
            logging.warn("Cleaning up %s", repo_dir)
            shutil.rmtree(config.clone_root / repo_dir)


def main():
    coloredlogs.install(
        level=logging.INFO,
        fmt="%(asctime)s %(levelname)s %(message)s",
    )
    config = Config.from_file(Path() / "repositories.toml")
    config.clone_root.mkdir(exist_ok=True)

    prune_repositories(config)
    check_repositories(config)

    while True:
        do_mirror(config)
        logging.info("Waiting %ds", config.interval)
        time.sleep(config.interval)


if __name__ == "__main__":
    main()
