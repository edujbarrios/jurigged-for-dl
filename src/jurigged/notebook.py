from __future__ import annotations

from dataclasses import dataclass
from types import FunctionType
from typing import Any, MutableMapping


@dataclass(frozen=True)
class PatchStats:
    functions_patched: int = 0
    classes_patched: int = 0
    functions_skipped: int = 0
    classes_skipped: int = 0

    def __add__(self, other: "PatchStats") -> "PatchStats":
        return PatchStats(
            functions_patched=self.functions_patched + other.functions_patched,
            classes_patched=self.classes_patched + other.classes_patched,
            functions_skipped=self.functions_skipped + other.functions_skipped,
            classes_skipped=self.classes_skipped + other.classes_skipped,
        )


def _same_origin(old: Any, new: Any, *, module_name: str | None) -> bool:
    if module_name is None:
        return True
    return getattr(old, "__module__", None) == module_name and getattr(
        new, "__module__", None
    ) == module_name


def patch_function(old: FunctionType, new: FunctionType) -> bool:
    """Patch a function in-place to behave like `new` while keeping identity."""
    if old is new:
        return True

    try:
        old.__code__ = new.__code__
    except ValueError:
        # Usually means a closure/freevar mismatch. We can't safely hot-swap that
        # while preserving identity.
        return False

    old.__defaults__ = new.__defaults__
    old.__kwdefaults__ = new.__kwdefaults__
    old.__annotations__ = getattr(new, "__annotations__", {})
    old.__doc__ = new.__doc__

    old.__dict__.clear()
    old.__dict__.update(new.__dict__)
    return True


def _unwrap_method_descriptor(obj: Any) -> tuple[str, FunctionType | None]:
    if isinstance(obj, FunctionType):
        return "function", obj
    if isinstance(obj, staticmethod):
        return "staticmethod", obj.__func__
    if isinstance(obj, classmethod):
        return "classmethod", obj.__func__
    return "other", None


def patch_class(old: type, new: type, *, allow_deletions: bool = False) -> PatchStats:
    """Patch a class in-place so existing instances pick up new methods."""
    if old is new:
        return PatchStats()

    stats = PatchStats()

    old.__doc__ = new.__doc__
    if hasattr(new, "__annotations__"):
        old.__annotations__ = getattr(new, "__annotations__")  # type: ignore[attr-defined]

    old_dict = old.__dict__
    new_dict = new.__dict__

    for name, new_value in new_dict.items():
        if name in {"__dict__", "__weakref__", "__module__", "__qualname__"}:
            continue

        if name in old_dict:
            old_value = old_dict[name]

            old_kind, old_fn = _unwrap_method_descriptor(old_value)
            new_kind, new_fn = _unwrap_method_descriptor(new_value)
            if old_fn is not None and new_fn is not None and old_kind == new_kind:
                if patch_function(old_fn, new_fn):
                    stats = stats + PatchStats(functions_patched=1)
                    # Keep the original descriptor object in-place (identity).
                    if old_kind == "function":
                        setattr(old, name, old_fn)
                    elif old_kind == "staticmethod":
                        setattr(old, name, staticmethod(old_fn))
                    elif old_kind == "classmethod":
                        setattr(old, name, classmethod(old_fn))
                else:
                    stats = stats + PatchStats(functions_skipped=1)
                continue

        setattr(old, name, new_value)

    if allow_deletions:
        for name in set(old_dict.keys()) - set(new_dict.keys()):
            if name.startswith("__") and name.endswith("__"):
                continue
            try:
                delattr(old, name)
            except Exception:
                pass

    stats = stats + PatchStats(classes_patched=1)
    return stats


def patch_namespace(
    before: MutableMapping[str, Any],
    after: MutableMapping[str, Any],
    *,
    module_name: str | None = "__main__",
) -> PatchStats:
    """Patch redefined objects so old references keep working.

    Typical usage is to snapshot a namespace before a notebook cell runs, then
    after execution patch any redefined functions/classes in-place and rebind
    the name to the original object.
    """
    stats = PatchStats()

    for name, old_obj in list(before.items()):
        if name not in after:
            continue
        new_obj = after[name]
        if old_obj is new_obj:
            continue

        if isinstance(old_obj, FunctionType) and isinstance(new_obj, FunctionType):
            if not _same_origin(old_obj, new_obj, module_name=module_name):
                continue
            if patch_function(old_obj, new_obj):
                after[name] = old_obj
                stats = stats + PatchStats(functions_patched=1)
            else:
                stats = stats + PatchStats(functions_skipped=1)

        elif isinstance(old_obj, type) and isinstance(new_obj, type):
            if not _same_origin(old_obj, new_obj, module_name=module_name):
                continue
            class_stats = patch_class(old_obj, new_obj)
            after[name] = old_obj
            stats = stats + class_stats
        else:
            continue

    return stats
