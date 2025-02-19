from __future__ import annotations
from functools import cached_property
import inspect
from types import MethodType
from typing import Any, TYPE_CHECKING, Callable, Iterable
import warnings
from docstring_parser import parse

if TYPE_CHECKING:
    from magicclass._gui import BaseGui

try:
    from typing import _BaseGenericAlias
except ImportError:
    from typing_extensions import _BaseGenericAlias

_type_like = (type, _BaseGenericAlias)

try:
    from types import GenericAlias

    _type_like += (GenericAlias,)
except ImportError:
    pass


def iter_members(cls: type, exclude_prefix: str = "__") -> Iterable[tuple[str, Any]]:
    """
    Iterate over all the members in the order of source code line number.
    This function is identical to inspect.getmembers except for the order
    of the results. We have to sort the name in the order of line number.
    """
    mro = (cls,) + inspect.getmro(cls)
    processed = set()
    names: list[str] = list(cls.__dict__.keys())
    try:
        for base in reversed(mro):
            for k in base.__dict__.keys():
                if k not in names:
                    names.append(k)

    except AttributeError:
        pass

    for key in names:
        try:
            value = getattr(cls, key)
            # handle the duplicate key
            if key in processed:
                raise AttributeError
        except AttributeError:
            for base in mro:
                if key in base.__dict__:
                    value = base.__dict__[key]
                    break
            else:
                continue
        if not key.startswith(exclude_prefix):
            yield key, value
        processed.add(key)


class Tooltips:
    """A class to manage dosctring based tooltips."""

    def __init__(self, obj: Any):
        self._doc = parse(obj.__doc__)

    @property
    def desc(self):
        doc = self._doc
        if doc.short_description is None:
            return ""
        elif doc.long_description is None:
            return doc.short_description
        else:
            return doc.short_description + "\n" + doc.long_description

    @cached_property
    def parameters(self) -> dict[str, str]:
        """Parse "Parameters" block to dict."""
        return dict(self._iter_args_of("param"))

    @cached_property
    def attributes(self) -> dict[str, str]:
        """Parse "Attributes" block to dict."""
        return dict(self._iter_args_of("attribute"))

    def _iter_args_of(self, type_name: str) -> Iterable[tuple[str, str]]:
        for p in self._doc.params:
            tp, name = p.args
            if tp == type_name:
                yield name, p.description


def get_signature(func) -> inspect.Signature:
    """Similar to ``inspect.signature`` but safely returns ``Signature``."""
    if hasattr(func, "__signature__"):
        sig = func.__signature__
    else:
        sig = inspect.signature(func)
    return sig


def argcount(func: Callable) -> int:
    """
    Count the number of parameters of a callable object.

    Basically, this function returns identical result as:
    >>> len(inspect.signature(func).parameters)
    but ~10x faster.
    """
    if hasattr(func, "__func__"):
        _func = func.__func__
    else:
        _func = func
    unwrapped: Callable = inspect.unwrap(
        _func, stop=(lambda f: hasattr(f, "__signature__"))
    )
    if hasattr(unwrapped, "__signature__"):
        nargs = len(unwrapped.__signature__.parameters)
    else:
        nargs = unwrapped.__code__.co_argcount
    if isinstance(func, MethodType):
        nargs -= 1
    return nargs


def get_level(f: Callable | type) -> int:
    level = f.__qualname__.split(_LOCALS)[-1].count(".")
    if callable(f):
        return level - 1
    return level


_LOCALS = "<locals>."


def is_instance_method(func: Callable) -> bool:
    """Check if a function is defined in a class."""
    return callable(func) and "." in func.__qualname__.split(_LOCALS)[-1]


def method_as_getter(self: BaseGui, getter: Callable):
    qualname = getter.__qualname__
    if _LOCALS in qualname:
        qualname = qualname.split(_LOCALS)[-1]
    *clsnames, funcname = qualname.split(".")
    self_cls = self.__class__.__qualname__.split(".")[-1]
    if self_cls not in clsnames:
        ns = ".".join(clsnames)
        raise ValueError(
            f"{self_cls} not in {clsnames!r}. "
            f"Method {funcname} is in namespace {ns!r}, so it is invisible "
            f"from class {self.__class__.__qualname__!r}."
        )
    i = clsnames.index(self_cls) + 1
    ins = self
    for clsname in clsnames[i:]:
        ins = getattr(ins, clsname)

    def _func(w):
        return getter(ins, w)

    return _func


def eval_attribute(obj: Any, literal: str):
    attrs = literal.split(".")
    out = obj
    for attr in attrs:
        out = getattr(out, attr)
    return out


def show_tree(ui: BaseGui) -> str:
    return _get_tree(ui)


def _get_tree(ui: BaseGui, depth: int = 0):
    pref = "\t" * depth
    children_str_list: list[str] = []
    for i, child in enumerate(ui.__magicclass_children__):
        text = _get_tree(child, depth=depth + 1)
        children_str_list.append(pref + f"\t{i:>3}: {text}")

    if children_str_list:
        children_str = "\n".join(children_str_list)
        out = f"'{ui.name}'\n{children_str}"
    else:
        out = f"'{ui.name}'"
    return out


def rst_to_html(rst: str, unescape: bool = True) -> str:
    """Convert rST string into HTML."""
    from docutils.examples import html_body

    try:
        body: bytes = html_body(rst, input_encoding="utf-8", output_encoding="utf-8")
        html = body.decode(encoding="utf-8")
        if unescape:
            from xml.sax.saxutils import unescape as _unescape

            html = _unescape(html)

    except Exception as e:
        warnings.warn(
            f"Could not convert string into HTML due to {type(e).__name__}: {e}",
            UserWarning,
        )
        html = rst
    return html


def copy_info(source: type):
    def wrapper(dst):
        _copy_info(source, dst)
        return dst

    return wrapper


def _copy_info(src: type, dst: type) -> None:
    if src.__doc__:
        dst.__doc__ = src.__doc__
    for name, attr in src.__dict__.items():
        if not hasattr(dst, name) or name.startswith("_"):
            continue
        dst_attr = getattr(dst, name)
        if isinstance(attr, type):
            # common inner class
            if not isinstance(dst_attr, type):
                raise TypeError(f"{name} type mismatch.")
            _copy_info(attr, dst_attr)
        elif callable(attr):
            # common method
            if not callable(dst_attr):
                raise TypeError(f"{name} type mismatch.")
            if hasattr(attr, "__signature__"):
                dst_attr.__signature__ = attr.__signature__
            if attr.__doc__:
                dst_attr.__doc__ = attr.__doc__

    return None


def is_type_like(x: Any) -> bool:
    return isinstance(x, _type_like) or hasattr(x, "__supertype__")
