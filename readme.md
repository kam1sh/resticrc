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
    ignore:
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
    keep:
      paths: .virtualenvs

after:
  forget:
    keep_daily: 14
    prune: true
  cmd: "rclone sync /backups/ yandex: backups"
```
It's beautiful, isn't it?

No?

Then look at the Python syntax!
```python
from resticrc.models import Repository, Job, Action
from resticrc import main

repo = Repository(name="host", path="/backups/host")

jobs = [
    Job(
        repo=repo, tag="gitea", action=Action(backup=["/var/lib/gitea", "/home/git"])
    )
]

main(repos=[repo], jobs=jobs)

```