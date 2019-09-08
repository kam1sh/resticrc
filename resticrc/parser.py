from pathlib import Path

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
import yaml

from .models import Repository, Job, Action


class Parser:
    """ Configuration parser. """
    def __init__(self, conf, read=True):
        self.conf = self.try_load(conf)
        self.global_settings = None
        self.repos = None
        self.jobs = None
        if read:
            self.read()

    def try_load(self, conf) -> dict:
        """ Tries to load conf object, if it's string or path-like object. """
        if isinstance(conf, dict):
            return conf
        pth = Path(conf)
        if not pth.exists():
            raise ValueError(f"Path {pth} does not exist.")
        with open(pth) as fd:
            return yaml.load(fd, Loader=Loader)

    def read(self):
        """ Reads configuration settings (global, repos, etc). """
        self.global_settings = self.conf.get("global", {})
        # dictionary for access to repos from parse_jobs()
        self.repos = self.parse_repos()
        self.jobs = self.parse_jobs()

    def parse_repos(self):
        value = self.conf.get("repos")
        if not value:
            raise ValueError(
                "Please define at lease one repository in mapping 'repos'."
            )
        out = {}
        return {name: Repository(name, path) for name, path in value.items()}

    def parse_jobs(self):
        return [self.parse_job(name, x) for name, x in self.conf.get("jobs", {}).items()]

    def parse_job(self, name, conf):
        if isinstance(conf, str):
            conf = dict(paths=[conf])
        paths = conf.pop("paths", None) or conf.pop("path", None)
        if isinstance(paths, str):
            paths = [paths]
        paths = None if paths == [] else paths
        action = Action(backup=paths, command=conf.get("cmd"), shell=conf.get("shell"))
        for k, v in self.global_settings.items():
            conf.setdefault(k, v)
        repo_name = conf.pop("repo")
        repo = self.repos[repo_name]
        return Job(tag=name, repo=repo, action=action, **conf)


def getlist(value) -> list:
    if isinstance(value, str):
        return [value]
    if hasattr(value, "__iter__"):
        return list(value)
    raise ValueError(f"Failed to convert {value} to list.")
