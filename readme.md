# Overview
Resticrc is a configuration interface to a restic backup tool.
Basically it converts YAML file to a restic command line arguments,
but resticrc does it really well and in some cases it can completely replace shell scripts.

Just look at the example configuration:
```yaml
# ~/.config/resticrc
repos: 
  host: /backups/host
  db: /backups/db

global:
  repo: host
  ignore:
    logs: true # *.log
    caches: true # .cache

jobs:
  gitea:
    paths:
      - /var/lib/gitea
      - /home/git
  etc: /etc
  data:
    path: /data
    ignore: vms
  postgresql:
    repo: db
    cmd: sudo -u postgres pg_dumpall
    save-as: postgres_dumpall
  home:
    path: /home
    exclude:
      dev-caches: true # includes python, npm, java, golang, rust, qt, and more
      # python: true # .pyenv, __pycache__, venv, .venv, .virtualenvs
      # npm: true # node_modules .npm/_cacache
      # java: true # .m2
      # golang: true # ~/go
      # note: golang exclusion will apply only on user who executes resticrc!
      # rust: true # .rustup .cargo
      # qt: true # .local/Qt
      trash: true # .local/share/Trash
      telegram: true # .local/share/TelegramDesktop
      paths:
        - ~/share
```
It's beautiful, isn't it?

No?

Then look at the Python syntax!
```python
from resticrc.models import Repository, Job
from resticrc.runner import FileRunner

repo = Repository(name="host", path="/backups/host")

job = Job(
    repo=repo,
    runner=FileRunner(paths=["/home/git", "/var/lib/gitea"]),
    tags=["gitea"],
    exclude={"logs": True}
)
job.run()
```

# Build

This tool uses [Poetry](https://python-poetry.org) for building:
```bash
poetry build
ls -l dist/resticrc-0.1.0-py3-none-any.whl
```
Also, there is super-puper-ultra-hyper build script for [PyOxidizer](https://github.com/indygreg/PyOxidizer):
```bash
pyoxidizer build
ls -l build/x86_64-unknown-linux-gnu/debug/install/
```
