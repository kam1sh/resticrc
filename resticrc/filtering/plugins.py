from .api import hookimpl, manager


class Logs:
    @hookimpl
    def exclude_hook(self, config):
        config.map("logs", "*.log")


manager.register(Logs())


class Caches:
    @hookimpl
    def exclude_hook(self, config):
        config.map(
            "caches",
            ".cache",
            ".config/*/Cache",
            ".config/*/GPUCache",
            ".config/*/CachedData",
            ".config/*/Code Cache",
            ".config/*/Service Worker/CacheStorage",
            ".config/*/*/Service Worker/CacheStorage",
            ".config/*/ShaderCache"
        )


manager.register(Caches())


class DevCaches:
    @hookimpl
    def exclude_hook(self, config):
        dev_caches = config.get("dev-caches")
        func = config.mapdefault if dev_caches else config.map
        func("python",
             ".pyenv",
             "__pycache__",
             ".venv",
             ".virtualenvs",
             ".cookiecutters",
             ".local/lib/python*/site-packages",
             ".local/share/pipenv/lib",
             ".local/share/virtualenvs"
        )
        func("npm", "node_modules", ".npm/_cacache")
        func("java", ".m2")
        func("golang", "/home/*/go")
        func("rust", ".rustup", ".cargo")
        func("ruby", ".gem")
        func("qt", ".local/Qt")
        func("pycharm", ".PyCharm*")


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
