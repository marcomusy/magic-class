from __future__ import annotations
from typing import Any, TYPE_CHECKING, Callable, TypeVar
from types import FunctionType

from magicgui import __version__ as _magicgui_version
from magicgui.widgets import FunctionGui, Widget
from magicclass._magicgui_compat import Undefined
from magicgui.type_map import get_widget_class
from magicgui.signature import magic_signature, MagicParameter

MAGICGUI_BEFORE_0_6 = _magicgui_version < "0.6"

if not MAGICGUI_BEFORE_0_6:
    from functools import partial

    # since magicgui 0.6, raise_on_unknown is newly implemented, which caused
    # inconsistency. See https://github.com/napari/magicgui/pull/476
    get_widget_class = partial(get_widget_class, raise_on_unknown=False)

from macrokit import Symbol

from magicclass.signature import split_annotated_type

if TYPE_CHECKING:
    from ._base import BaseGui
    from magicgui.widgets import FunctionGui, FileEdit


def get_parameters(fgui: FunctionGui):
    return {k: v.default for k, v in fgui.__signature__.parameters.items()}


_C = TypeVar("_C", bound=type)


def copy_class(cls: _C, ns: type, name: str | None = None) -> _C:
    """
    Copy a class in a new namespace.

    This function not only copies the class object but also update all the
    ``__qualname__`` recursively.

    Parameters
    ----------
    cls : type
        Class to be copied.
    ns : type
        New namespace of ``cls``.
    name : str, optional
        New name of ``cls``. If not given, the original name will be used.

    Returns
    -------
    type
        Copied class object.
    """
    out = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
    if name is None:
        name = out.__name__
    _update_qualnames(out, f"{ns.__qualname__}.{name}")
    return out


def _update_qualnames(cls: type, cls_qualname: str) -> None:
    cls.__qualname__ = cls_qualname
    # NOTE: updating cls.__name__ will make `wraps` incompatible.
    for key, attr in cls.__dict__.items():
        if isinstance(attr, FunctionType):
            attr.__qualname__ = f"{cls_qualname}.{key}"
        elif isinstance(attr, type):
            _update_qualnames(attr, f"{cls_qualname}.{key}")

    return None


class MagicClassConstructionError(Exception):
    """Raised when class definition is not a valid magic-class."""


def format_error(
    e: Exception,
    hist: list[tuple[str, str, str]],
    name: str,
    attr: Any,
):
    hist_str = (
        "\n\t".join(map(lambda x: f"{x[0]} {x[1]} -> {x[2]}", hist))
        + f"\n\t\t{name} ({type(attr)}) <--- Error"
    )
    if not hist_str.startswith("\n\t"):
        hist_str = "\n\t" + hist_str
    if isinstance(e, MagicClassConstructionError):
        e.args = (f"\n{hist_str}\n{e}",)
        raise e
    else:
        tb = e.__traceback__
        construction_err = MagicClassConstructionError(
            f"\n{hist_str}\n\n{type(e).__name__}: {e}"
        ).with_traceback(tb)
        raise construction_err from None


def connect_magicclasses(parent: BaseGui, child: BaseGui, child_name: str):
    """Connect magicclass parent/child."""

    child.__magicclass_parent__ = parent
    parent.__magicclass_children__.append(child)
    child._my_symbol = Symbol(child_name)


def callable_to_classes(f: Callable) -> list[type[Widget]]:
    """Get list of classes that will be generated by the magicgui type map."""
    sig = magic_signature(f)
    return [_parameter_to_widget_class(p) for p in sig.parameters.values()]


def show_dialog_from_mgui(mgui: FunctionGui):
    """Show file dialog from given magicgui widget."""
    fdialog: FileEdit = mgui[0]
    if result := fdialog._show_file_dialog(
        fdialog.mode,
        caption=fdialog._btn_text,
        start_path=str(fdialog.value),
        filter=fdialog.filter,
    ):
        fdialog.value = result
        out = mgui(result)
    else:
        out = None
    return out


TZ_EMPTY = "__no__default__"


def _parameter_to_widget_class(param: MagicParameter):
    value = Undefined if param.default in (param.empty, TZ_EMPTY) else param.default
    annotation, options = split_annotated_type(param.annotation)
    options = options.copy()
    wdg_class, _ = get_widget_class(value, annotation, options)
    return wdg_class
