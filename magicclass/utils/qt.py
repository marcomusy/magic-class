from __future__ import annotations
from qtpy.QtWidgets import QMessageBox, QWidget
from qtpy import QtGui
from enum import Enum


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


def screen_center():
    """Get the center coordinate of the screen."""
    _screen_rect = QtGui.QGuiApplication.primaryScreen().geometry()
    return _screen_rect.center()


def move_to_screen_center(qwidget: QWidget) -> None:
    """Move a QWidget to the center of screen."""
    point = screen_center() - qwidget.rect().center()
    qwidget.move(point)
    qwidget.adjustSize()
    return None


def screen_scale() -> float:
    """Get the scale of main screen."""
    from qtpy.QtGui import QGuiApplication

    screen = QGuiApplication.screens()[0]
    return screen.devicePixelRatio()


def to_clipboard(obj) -> None:
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
        if obj.ndim == 3:
            if obj.shape[2] == 3:
                qimg_format = QImage.Format.Format_RGB888
            elif obj.shape[2] == 4:
                qimg_format = QImage.Format.Format_RGBA8888
            else:
                raise ValueError(
                    "Can only copy an array of shape (..., 3) or (..., 4)."
                )
        else:
            if obj.ndim != 2:
                raise ValueError("Can only copy 2D or 3D array")
            qimg_format = QImage.Format.Format_Indexed8

        h, w, *_ = obj.shape
        obj = np.ascontiguousarray(obj)
        qimg = QImage(obj.data, w, h, int(obj.strides[0]), qimg_format)
        gray_color_table = [qRgb(i, i, i) for i in range(256)]
        qimg.setColorTable(gray_color_table)
        clipboard.setImage(qimg)
    elif isinstance(obj, pd.DataFrame):
        clipboard.setText(obj.to_csv(sep="\t"))
    else:
        clipboard.setText(str(obj))
