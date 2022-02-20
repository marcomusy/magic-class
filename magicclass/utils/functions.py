from __future__ import annotations
import inspect
from enum import Enum
from typing import Any
from docstring_parser import parse
from qtpy.QtWidgets import QApplication, QMessageBox

__all__ = [
    "MessageBoxMode",
    "show_messagebox",
    "open_url",
    "screen_center",
    "to_clipboard",
    "iter_members",
    "extract_tooltip",
    "get_signature",
]


def iter_members(cls: type, exclude_prefix: str = "__") -> list[str, Any]:
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


def extract_tooltip(obj: Any) -> str:
    """Extract docstring for tooltip."""
    doc = parse(obj.__doc__)
    if doc.short_description is None:
        return ""
    elif doc.long_description is None:
        return doc.short_description
    else:
        return doc.short_description + "\n" + doc.long_description


def get_signature(func):
    """Similar to ``inspect.signature`` but safely returns ``Signature``."""
    if hasattr(func, "__signature__"):
        sig = func.__signature__
    else:
        sig = inspect.signature(func)
    return sig


class MessageBoxMode(Enum):
    ERROR = "error"
    WARNING = "warn"
    INFO = "info"
    QUESTION = "question"
    ABOUT = "about"


_QMESSAGE_MODES = {
    MessageBoxMode.ERROR: QMessageBox.critical,
    MessageBoxMode.WARNING: QMessageBox.warning,
    MessageBoxMode.INFO: QMessageBox.information,
    MessageBoxMode.QUESTION: QMessageBox.question,
    MessageBoxMode.ABOUT: QMessageBox.about,
}


def show_messagebox(
    mode: str | MessageBoxMode = MessageBoxMode.INFO,
    title: str = None,
    text: str = None,
    parent=None,
) -> bool:
    """
    Freeze the GUI and open a messagebox dialog.

    Parameters
    ----------
    mode : str or MessageBoxMode, default is MessageBoxMode.INFO
        Mode of message box. Must be "error", "warn", "info", "question" or "about".
    title : str, optional
        Title of messagebox.
    text : str, optional
        Text in messagebox.
    parent : QWidget, optional
        Parent widget.

    Returns
    -------
    bool
        If "OK" or "Yes" is clicked, return True. Otherwise return False.
    """
    show_dialog = _QMESSAGE_MODES[MessageBoxMode(mode)]
    result = show_dialog(parent, title, text)
    return result in (QMessageBox.Ok, QMessageBox.Yes)


def open_url(link: str) -> None:
    """
    Open the link with the default browser.

    Parameters
    ----------
    link : str
        Link to the home page.
    """
    from qtpy.QtGui import QDesktopServices
    from qtpy.QtCore import QUrl

    QDesktopServices.openUrl(QUrl(link))


def to_clipboard(obj: Any) -> None:
    """
    Copy an object of any type to the clipboard.
    You can copy text, ndarray as an image or data frame as a table data.

    Parameters
    ----------
    obj : Any
        Object to be copied.
    """
    from qtpy.QtGui import QGuiApplication, QImage, qRgb
    import numpy as np
    import pandas as pd

    clipboard = QGuiApplication.clipboard()

    if isinstance(obj, str):
        clipboard.setText(obj)
    elif isinstance(obj, np.ndarray):
        if obj.dtype != np.uint8:
            raise ValueError(f"Cannot copy an array of dtype {obj.dtype} to clipboard.")
        # See https://gist.github.com/smex/5287589
        qimg_format = QImage.Format_RGB888 if obj.ndim == 3 else QImage.Format_Indexed8
        *_, h, w = obj.shape
        qimg = QImage(obj.data, w, h, obj.strides[0], qimg_format)
        gray_color_table = [qRgb(i, i, i) for i in range(256)]
        qimg.setColorTable(gray_color_table)
        clipboard.setImage(qimg)
    elif isinstance(obj, pd.DataFrame):
        clipboard.setText(obj.to_csv(sep="\t"))
    else:
        clipboard.setText(str(obj))


def screen_center():
    """
    Get the center coordinate of the screen.
    """
    return QApplication.desktop().screen().rect().center()
