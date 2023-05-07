from magicgui import magicgui
from magicclass import magicclass, vfield
from magicclass.undo import undo_callback

def test_undo_func():
    @magicclass
    class A:
        def __init__(self):
            self._x = 0

        def f(self, x: int):
            old_value = self._x
            self._x = x
            @undo_callback
            def undo():
                self._x = old_value
            return undo

    ui = A()
    ui.f(1)
    ui.f(2)
    assert ui._x == 2
    assert len(ui.macro) == 3 and str(ui.macro[-1]) == "ui.f(x=2)"

    ui.macro.undo()
    assert ui._x == 1
    assert len(ui.macro) == 2 and str(ui.macro[-1]) == "ui.f(x=1)"
    ui.macro.undo()
    assert ui._x == 0
    assert len(ui.macro) == 1 and str(ui.macro[-1])
    ui.macro.redo()
    assert ui._x == 1
    assert len(ui.macro) == 2 and str(ui.macro[-1]) == "ui.f(x=1)"
    ui.macro.redo()
    assert ui._x == 2
    assert len(ui.macro) == 3 and str(ui.macro[-1]) == "ui.f(x=2)"

    ui.macro.undo()
    assert ui._x == 1
    assert len(ui.macro) == 2 and str(ui.macro[-1]) == "ui.f(x=1)"
    ui.macro.undo()
    assert ui._x == 0
    assert len(ui.macro) == 1 and str(ui.macro[-1])
    ui.macro.redo()
    assert ui._x == 1
    assert len(ui.macro) == 2 and str(ui.macro[-1]) == "ui.f(x=1)"
    ui.macro.redo()
    assert ui._x == 2
    assert len(ui.macro) == 3 and str(ui.macro[-1]) == "ui.f(x=2)"


def test_magicgui_undo():
    @magicclass
    class A:
        def __init__(self) -> None:
            self._x = 0

        @magicgui
        def f(self, x: int):
            old_value = self._x
            self._x = x
            @undo_callback
            def undo():
                self._x = old_value
            return undo

    ui = A()
    ui[0].x.value = 1
    ui[0].call_button.changed()
    ui[0].x.value = 2
    ui[0].call_button.changed()
    assert ui._x == 2
    assert len(ui.macro) == 3 and str(ui.macro[-1]) == "ui.f(x=2)"
    ui.macro.undo()
    assert ui._x == 1
    assert len(ui.macro) == 2 and str(ui.macro[-1]) == "ui.f(x=1)"
    ui.macro.undo()
    assert ui._x == 0
    assert len(ui.macro) == 1
    ui.macro.redo()
    assert ui._x == 1
    assert len(ui.macro) == 2 and str(ui.macro[-1]) == "ui.f(x=1)"
    ui.macro.redo()
    assert ui._x == 2
    assert len(ui.macro) == 3 and str(ui.macro[-1]) == "ui.f(x=2)"

def test_clear_undo_stack():
    @magicclass
    class A:
        x = vfield(10)

        def undoable(self):
            return undo_callback(lambda: None)

        def not_undoable(self):
            pass

    ui = A()
    ui.x = 20
    ui.not_undoable()
    assert len(ui.macro._stack_undo) == 0
    ui.undoable()
    ui.undoable()
    ui.macro.undo()
    assert len(ui.macro._stack_undo) == len(ui.macro._stack_redo) == 1
    ui.not_undoable()
    assert len(ui.macro._stack_undo) == len(ui.macro._stack_redo) == 0

def test_autocall_method():
    from magicclass import set_options, get_function_gui

    @magicclass
    class A:
        def __init__(self) -> None:
            self._x = 0

        @set_options(auto_call=True)
        def f(self, x: int):
            old_value = self._x
            self._x = x
            @undo_callback
            def undo():
                self._x = old_value
            return undo

        def g(self):
            @undo_callback
            def undo():
                pass
            return undo

    ui = A()
    fgui = get_function_gui(ui.f)
    fgui.x.value = 1
    fgui.x.value = 2
    fgui.x.value = 3
    assert ui._x == 3
    ui.macro.undo()
    assert ui._x == 0

def test_undo_thread_worker():
    from magicclass.utils import thread_worker

    @magicclass
    class A:
        def __init__(self) -> None:
            self._x = 0

        @thread_worker
        def f(self, x: int):
            old_value = self._x
            self._x = x
            @undo_callback
            def out():
                self._x = old_value
            return out

    ui = A()
    ui.f(1)
    ui.f(2)
    assert ui._x == 2
    assert len(ui.macro) == 3 and str(ui.macro[-1]) == "ui.f(x=2)"
    ui.macro.undo()
    assert ui._x == 1
    assert len(ui.macro) == 2 and str(ui.macro[-1]) == "ui.f(x=1)"
    ui.macro.undo()
    assert ui._x == 0
    assert len(ui.macro) == 1 and str(ui.macro[-1])
    ui.macro.redo()
    assert ui._x == 1
    assert len(ui.macro) == 2 and str(ui.macro[-1]) == "ui.f(x=1)"
    ui.macro.redo()
    assert ui._x == 2
    assert len(ui.macro) == 3 and str(ui.macro[-1]) == "ui.f(x=2)"

def test_undoable_in_undo():
    @magicclass
    class A:
        def __init__(self):
            self._values = []

        def add_value(self, x: int):
            self._values.append(x)
            @undo_callback
            def out():
                self.pop_value()
            return out

        def pop_value(self):
            val = self._values.pop()
            @undo_callback
            def out():
                self.add_value(val)
            return out

    ui = A()
    ui.add_value(1)
    ui.add_value(2)
    assert ui._values == [1, 2]
    ui.macro.undo()
    assert ui._values == [1]
    ui.macro.undo()
    assert ui._values == []
    ui.macro.undo()
    assert ui._values == []
    ui.macro.redo()
    assert ui._values == [1]
    ui.macro.redo()
    assert ui._values == [1, 2]
    ui.macro.redo()
    assert ui._values == [1, 2]
    ui.macro.undo()
    assert ui._values == [1]
    ui.macro.undo()
    assert ui._values == []
    ui.macro.undo()
    assert ui._values == []
    ui.macro.redo()
    assert ui._values == [1]
    ui.macro.redo()
    assert ui._values == [1, 2]
    ui.macro.redo()
    assert ui._values == [1, 2]
