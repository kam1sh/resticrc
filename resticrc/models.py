from typing import List, Optional

from attr import attrs, attrib


@attrs
class Repository:
    name: str = attrib()
    path: str = attrib()


@attrs
class Action:
    backup: Optional[List[str]] = attrib(default=None)
    command: Optional[str] = attrib(default=None)
    shell: Optional[str] = attrib(default=None)


@attrs
class Job:
    repo: Repository = attrib()
    tag: Optional[str] = attrib()
    exclude: Optional[dict] = attrib(default=None)
    action: Optional[Action] = attrib(default=None)
