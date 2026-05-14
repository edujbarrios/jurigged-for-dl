from codefind import ConformException, code_registry as db

from .codetools import CodeFile
from .live import Watcher, watch
from .recode import Recoder, make_recoder, virtual_file
from .register import registry
from .utils import glob_filter
from .version import version as __version__


def load_ipython_extension(ipython):  # pragma: no cover
    from .notebook import load_ipython_extension as _load

    return _load(ipython)


def unload_ipython_extension(ipython):  # pragma: no cover
    from .notebook import unload_ipython_extension as _unload

    return _unload(ipython)


__all__ = [
    "ConformException",
    "db",
    "CodeFile",
    "Watcher",
    "watch",
    "Recoder",
    "make_recoder",
    "virtual_file",
    "registry",
    "glob_filter",
    "load_ipython_extension",
    "unload_ipython_extension",
    "__version__",
]
