from __future__ import annotations
from typing import Callable
import warnings
from magicgui.widgets import Image, Table, Label, FunctionGui, Widget
from magicgui.widgets.bases import ButtonWidget
from macrokit import Symbol
from psygnal import Signal
from qtpy.QtCore import Qt

from .mgui_ext import (
    AbstractAction,
    WidgetAction,
    _LabeledWidgetAction,
    QMenu,
)
from .keybinding import register_shortcut
from ._base import (
    BaseGui,
    PopUpMode,
    ErrorMode,
    ContainerLikeGui,
    normalize_insertion,
)
from .utils import format_error

from magicclass.signature import get_additional_option
from magicclass.widgets import Separator, FreeWidget
from magicclass.utils import iter_members, Tooltips


def _check_popupmode(popup_mode: PopUpMode):
    if popup_mode in (PopUpMode.above, PopUpMode.below, PopUpMode.first):
        msg = (
            f"magicmenu does not support popup mode {popup_mode.value}."
            "PopUpMode.popup is used instead"
        )
        warnings.warn(msg, UserWarning)
    elif popup_mode == PopUpMode.last:
        msg = (
            f"magicmenu does not support popup mode {popup_mode.value}."
            "PopUpMode.parentlast is used instead"
        )
        warnings.warn(msg, UserWarning)
        popup_mode = PopUpMode.parentlast

    return popup_mode


class MenuGuiBase(ContainerLikeGui):
    def __init__(
        self,
        parent=None,
        name: str = None,
        close_on_run: bool = None,
        popup_mode: str | PopUpMode = None,
        error_mode: str | ErrorMode = None,
        labels: bool = True,
    ):
        popup_mode = _check_popupmode(popup_mode)

        super().__init__(
            close_on_run=close_on_run, popup_mode=popup_mode, error_mode=error_mode
        )
        name = name or self.__class__.__name__
        self._native = QMenu(name, parent)
        self.native.setToolTipsVisible(True)
        self.name = name
        self._list: list[MenuGuiBase | AbstractAction] = []
        self.labels = labels
        self._native._palette_event_filter.paletteChanged.connect(self._update_icon)

    @property
    def native(self):
        """The native Qt widget."""
        return self._native

    def _convert_attributes_into_widgets(self):
        cls = self.__class__

        # Add class docstring as tooltip.
        _tooltips = Tooltips(cls)
        self.tooltip = _tooltips.desc

        # Bind all the methods and annotations
        base_members = {x[0] for x in iter_members(MenuGuiBase)}

        _hist: list[tuple[str, str, str]] = []  # for traceback
        _ignore_types = (property, classmethod, staticmethod)

        for name, attr in filter(lambda x: x[0] not in base_members, iter_members(cls)):
            if isinstance(attr, _ignore_types):
                continue

            try:
                widget = self._convert_an_attribute_into_widget(name, attr, _tooltips)

                if isinstance(widget, BaseGui):
                    if isinstance(widget, MenuGuiBase):
                        widget.native.setParent(
                            self.native, widget.native.windowFlags()
                        )
                    else:
                        widget = WidgetAction(widget)

                elif isinstance(widget, Widget):
                    if not widget.name:
                        widget.name = name
                    if hasattr(widget, "text") and not widget.text:
                        widget.text = widget.name.replace("_", " ")
                    widget = WidgetAction(widget)

                if isinstance(widget, (MenuGuiBase, AbstractAction, Callable, Widget)):
                    if (not isinstance(widget, Widget)) and callable(widget):
                        if name.startswith("_") or not get_additional_option(
                            attr, "gui", True
                        ):
                            keybinding = get_additional_option(attr, "keybinding", None)
                            if keybinding:
                                register_shortcut(
                                    keys=keybinding, parent=self.native, target=widget
                                )
                            continue
                        if isinstance(widget, Signal):
                            continue
                        widget = self._create_widget_from_method(widget)

                    elif hasattr(widget, "__magicclass_parent__") or hasattr(
                        widget.__class__, "__magicclass_parent__"
                    ):
                        if isinstance(widget, BaseGui):
                            widget._my_symbol = Symbol(name)
                        # magic-class has to know its parent.
                        # if __magicclass_parent__ is defined as a property, hasattr
                        # must be called with a type object (not instance).
                        widget.__magicclass_parent__ = self

                    if widget.name.startswith("_"):
                        continue
                    moveto = get_additional_option(attr, "into")
                    copyto = get_additional_option(attr, "copyto", [])
                    if moveto is not None or copyto:
                        self._unwrap_method(name, widget, moveto, copyto)
                    else:
                        self._fast_insert(len(self), widget)

                    _hist.append((name, str(type(attr)), type(widget).__name__))

            except Exception as e:
                format_error(e, _hist, name, attr)

        self._unify_label_widths()
        return None

    def _fast_insert(
        self,
        key: int,
        obj: Callable | MenuGuiBase | AbstractAction | Widget,
        remove_label: bool = False,
    ) -> None:
        _obj = normalize_insertion(self, obj)

        if isinstance(_obj, Widget):
            _obj = WidgetAction(_obj)

        if isinstance(_obj, (self._component_class, MenuGuiBase)):
            insert_action_like(self.native, key, _obj.native)
            self._list.insert(key, _obj)

        elif isinstance(_obj, WidgetAction):
            from .toolbar import ToolBarGui

            if isinstance(_obj.widget, Separator):
                insert_action_like(self.native, key, _obj.widget.title)

            elif isinstance(_obj.widget, ToolBarGui):
                qmenu = QMenu(_obj.widget.name, self.native)
                qmenu.addAction(_obj.native)
                if _obj.widget.icon is not None:
                    qicon = _obj.widget.icon.get_qicon(qmenu)
                    qmenu.setIcon(qicon)
                insert_action_like(self.native, key, qmenu)

            else:
                _hide_labels = (
                    _LabeledWidgetAction,
                    ButtonWidget,
                    FreeWidget,
                    Label,
                    FunctionGui,
                    Image,
                    Table,
                )
                _obj_labeled = _obj
                if self.labels:
                    if not isinstance(_obj.widget, _hide_labels) and not remove_label:
                        _obj_labeled = _LabeledWidgetAction.from_action(_obj)
                _obj_labeled.parent = self
                insert_action_like(self.native, key, _obj_labeled.native)

            self._list.insert(key, _obj)
        else:
            raise TypeError(f"{type(_obj)} is not supported.")

    def insert(self, key: int, obj: Callable | MenuGuiBase | AbstractAction) -> None:
        """
        Insert object into the menu. Could be widget or callable.

        Parameters
        ----------
        key : int
            Position to insert.
        obj : Callable | MenuGuiBase | AbstractAction | Widget
            Object to insert.
        """
        self._fast_insert(key, obj)
        self._unify_label_widths()


def insert_action_like(qmenu: QMenu, key: int, obj):
    """
    Insert a QObject into a QMenu in a Pythonic way, like qmenu.insert(key, obj).

    Parameters
    ----------
    qmenu : QMenu
        QMenu object to which object will be inserted.
    key : int
        Position to insert.
    obj : QMenu or QAction or str
        Object to be inserted.
    """
    actions = qmenu.actions()
    nactions = len(actions)
    if key in (nactions, -1):
        if isinstance(obj, QMenu):
            qmenu.addMenu(obj).setText(obj.objectName().replace("_", " "))
        elif isinstance(obj, str):
            if obj:
                qmenu.addSection(obj)
            else:
                qmenu.addSeparator()
        else:
            qmenu.addAction(obj)
    else:
        before = actions[key]
        if isinstance(obj, QMenu):
            qmenu.insertMenu(before, obj).setText(obj.objectName().replace("_", " "))
        elif isinstance(obj, str):
            if obj:
                qmenu.insertSection(before, obj)
            else:
                qmenu.insertSeparator(before)
        else:
            qmenu.insertAction(before, obj)


class MenuGui(MenuGuiBase):
    """Magic class that will be converted into a menu bar."""


class ContextMenuGui(MenuGuiBase):
    """Magic class that will be converted into a context menu."""

    def _set_magic_context_menu(self, parent: Widget | BaseGui) -> None:
        parent.native.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        @parent.native.customContextMenuRequested.connect
        def rightClickContextMenu(point):
            self.native.exec_(parent.native.mapToGlobal(point))

        return None
