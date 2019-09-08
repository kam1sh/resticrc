import typing as ty
import logging
from pathlib import Path

import pluggy


hookspec = pluggy.HookspecMarker("resticrc")
hookimpl = pluggy.HookimplMarker("resticrc")
manager = pluggy.PluginManager("resticrc")
log = logging.getLogger(__name__)


def _parse_path(path: str):
    if path.startswith("~/"):
        path = str(Path.home().joinpath(path[2:]).absolute())
    return path


class IgnoreConfig(dict):
    def __init__(self, items):
        super().__init__(items)
        self.pluginmap: ty.Dict[str, ty.Union[ty.Tuple[str]], Holder] = {}

    def map(self, name, *paths):
        val = self.get(name)
        if val is None:
            return
        # if user send True, then add paths as is
        # to filtering them in the future
        # if False, then mark paths as explicit include
        self.pluginmap[name] = paths if val else Keep(paths)

    def mapdefault(self, k, *defaults):
        return self.pluginmap.setdefault(k, Default(defaults))

    def get_result(self) -> ty.Iterator[str]:
        result = []
        keep: ty.List[str] = []
        # 1. populate paths
        for key, item in self.pluginmap.items():
            if isinstance(item, Holder):
                item.action(key, self, keep, result)
                continue
            result.extend(item)
        # 2. filtering what should be kept
        for item in keep:
            if item in result:
                # TODO check strings contents?
                result.remove(item)
        return map(_parse_path, result)

    def render(self):
        return "\n".join(self.get_result())

    def __str__(self):
        return self.render()


# I decided not to use nested dicts like {"python": {"paths": ..., "type": "keep"}},
# but to have class-holders, so checks could be made via isinstance(val, Keep) etc
class Holder:
    def __init__(self, value):
        self.value = value

    def action(self, name, config, keep, result):
        raise NotImplementedError


class Keep(Holder):
    """Holder that indicates that paths should be kept (excluded from exclusion)"""

    def action(self, name, config, keep, result):
        keep.extend(self.value)


class Default(Holder):
    """
    Holder for default values. Useful, when your plugin defines multiple ignores
    and user may want to filtering some of them.
    """

    def action(self, name, config, keep, result):
        # set value if item specified in config
        val = config.get(name)
        if val in (True, None):
            result.extend(self.value)
        else:
            keep.extend(self.value)


class IgnoreCase(Holder):
    def action(self, name, config, keep, result):
        result.append(self)


class PluginSpecification:
    @hookspec
    def exclude_hook(self, config: IgnoreConfig):
        """
        Hook for customising files exclusion.
        :argument config: IgnoreConfig object.
        Examples:
            def exclude_caches(config, pluginmap):
                # If 'skip' mapping in user config contains
                #'caches', then ".cache", "*Cache" etc will be skipped.
                config.map("caches", ".cache", "*Cache*", *cache*")
                # Or with ignore case
                config.map("caches", IgnoreCase("*cache*"))
        """


manager.add_hookspecs(PluginSpecification)


def process_filters(config: dict):
    """ Returns what paths should be excluded """
    config = IgnoreConfig(config)
    manager.hook.exclude_hook(config=config)
    return config


