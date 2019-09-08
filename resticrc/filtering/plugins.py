from .api import hookimpl, manager, IgnoreCase

class Logs:
    @hookimpl
    def exclude_hook(self, config):
        config.map("logs", "*.log")


manager.register(Logs())


class Caches:
    @hookimpl
    def exclude_hook(self, config):
        config.map("caches", IgnoreCase("*cache*"))


manager.register(Caches())


class DevCaches:
    @hookimpl
    def exclude_hook(self, config):
        dev_caches = config.get("dev-caches")
        func = config.mapdefault if dev_caches else config.map
        func("python", ".pyenv", "__pycache__", ".venv", ".virtualenvs")
        func("npm", "node_modules", ".npm/_cacache")
        func("java", ".m2")
        func("golang", "~/go")
        func("rust", ".rustup", ".cargo")
        func("qt", ".local/Qt")


manager.register(DevCaches())


class Trash:
    @hookimpl
    def exclude_hook(self, config):
        config.map("trash", ".local/share/Trash")


manager.register(Trash())


class Telegram:
    @hookimpl
    def exclude_hook(self, config):
        config.map("telegram", ".local/share/TelegramDesktop")


manager.register(Telegram())
