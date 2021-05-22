import hashlib
import logging
import os
import urllib.request
from pathlib import Path
from typing import List, Optional

import toml
from pydantic import BaseModel, HttpUrl, ValidationError


class Repository(BaseModel):
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


class Config(BaseModel):
    repository: List[Repository]
    clone_root: Path = Path().resolve() / "repos"
    heartbeat: Optional[HttpUrl] = None
    interval: int = 900

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
