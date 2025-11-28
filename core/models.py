from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Repository:
    repo_id: str
    name_with_owner: str
    repo_name: str
    owner_login: str
    url: str
    stars: int
    fetched_at: datetime
