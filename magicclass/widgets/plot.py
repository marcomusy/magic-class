from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Callable,
    TypeVar,
)
from typing_extensions import ParamSpec

from .utils import FreeWidget

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.lines import Line2D
    from matplotlib.collections import PathCollection
    from matplotlib.text import Text
    from matplotlib.quiver import Quiver
    from matplotlib.legend import Legend
    from numpy.typing import ArrayLike

try:
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from ._mpl_canvas import InteractiveFigureCanvas

    _P = ParamSpec("_P")
    _R = TypeVar("_R")

    def _inject_mpl_docs(f: Callable[_P, _R]) -> Callable[_P, _R]:
        plt_func = getattr(plt, f.__name__)
        f.__annotations__ = {"self": "Figure"}.update(plt_func.__annotations__)
        plt_doc = getattr(plt_func, "__doc__", "")
        if plt_doc:
            f.__doc__ = f"Copy of ``plt.{f.__name__}()``. Original docstring is ...\n\n{plt_doc}"
        return f

except ImportError as e:

    def _inject_mpl_docs(f: Callable[_P, _R]) -> Callable[_P, _R]:
        return f


class Figure(FreeWidget):
    """A matplotlib figure canvas."""

    def __init__(
        self,
        nrows: int = 1,
        ncols: int = 1,
        figsize: tuple[float, float] = (4.0, 3.0),
        style=None,
        **kwargs,
    ):
        backend = mpl.get_backend()
        try:
            mpl.use("Agg")
            if style is None:
                fig, _ = plt.subplots(nrows, ncols, figsize=figsize)
            else:
                with plt.style.context(style):
                    fig, _ = plt.subplots(nrows, ncols, figsize=figsize)
        finally:
            mpl.use(backend)

        canvas = InteractiveFigureCanvas(fig)
        self.canvas = canvas
        super().__init__(**kwargs)
        self.set_widget(canvas)
        self.figure = fig
        self.min_height = 40

    @_inject_mpl_docs
    def draw(self):
        self.figure.tight_layout()
        self.canvas.draw()

    @property
    def enabled(self) -> bool:
        """toggle interactivity of the figure canvas."""
        return self.canvas._interactive

    @enabled.setter
    def enabled(self, v: bool):
        self.canvas._interactive = bool(v)

    @property
    def mouse_click_callbacks(self) -> list[Callable]:
        return self.canvas._mouse_click_callbacks

    interactive = enabled  # alias

    @_inject_mpl_docs
    def clf(self) -> None:
        self.figure.clf()
        self.draw()

    @_inject_mpl_docs
    def cla(self) -> None:
        self.ax.cla()
        self.draw()

    @property
    def axes(self) -> list[Axes]:
        """List of matplotlib axes."""
        return self.figure.axes

    @property
    def ax(self) -> Axes:
        """The first matplotlib axis."""
        try:
            _ax = self.axes[0]
        except IndexError:
            _ax = self.figure.add_subplot(111)
        return _ax

    @_inject_mpl_docs
    def subplots(
        self, *args, **kwargs
    ) -> tuple[Figure, Axes] | tuple[Figure, list[Axes]]:
        self.clf()
        fig = self.figure
        axs = fig.subplots(*args, **kwargs)
        self.draw()
        return fig, axs

    @_inject_mpl_docs
    def savefig(self, *args, **kwargs) -> None:
        return self.figure.savefig(*args, **kwargs)

    @_inject_mpl_docs
    def plot(self, *args, **kwargs) -> list[Line2D]:
        lines = self.ax.plot(*args, **kwargs)
        self.draw()
        return lines

    @_inject_mpl_docs
    def scatter(self, *args, **kwargs) -> PathCollection:
        paths = self.ax.scatter(*args, **kwargs)
        self.draw()
        return paths

    @_inject_mpl_docs
    def hist(
        self, *args, **kwargs
    ) -> tuple[ArrayLike | list[ArrayLike], ArrayLike, list | list[list]]:
        out = self.ax.hist(*args, **kwargs)
        self.draw()
        return out

    @_inject_mpl_docs
    def text(self, *args, **kwargs) -> Text:
        text = self.ax.text(*args, **kwargs)
        self.draw()
        return text

    @_inject_mpl_docs
    def quiver(self, *args, data=None, **kwargs) -> Quiver:
        quiver = self.ax.quiver(*args, data=data, **kwargs)
        self.draw()
        return quiver

    @_inject_mpl_docs
    def axline(self, xy1, xy2=None, *, slope=None, **kwargs) -> Line2D:
        lines = self.ax.axline(xy1, xy2=xy2, slope=slope, **kwargs)
        self.draw()
        return lines

    @_inject_mpl_docs
    def axhline(self, y=0, xmin=0, xmax=1, **kwargs) -> Line2D:
        lines = self.ax.axhline(y, xmin, xmax, **kwargs)
        self.draw()
        return lines

    @_inject_mpl_docs
    def axvline(self, x=0, ymin=0, ymax=1, **kwargs) -> Line2D:
        lines = self.ax.axvline(x, ymin, ymax, **kwargs)
        self.draw()
        return lines

    @_inject_mpl_docs
    def xlim(self, *args, **kwargs) -> tuple[float, float]:
        ax = self.ax
        if not args and not kwargs:
            return ax.get_xlim()
        ret = ax.set_xlim(*args, **kwargs)
        self.draw()
        return ret

    @_inject_mpl_docs
    def ylim(self, *args, **kwargs) -> tuple[float, float]:
        ax = self.ax
        if not args and not kwargs:
            return ax.get_ylim()
        ret = ax.set_ylim(*args, **kwargs)
        self.draw()
        return ret

    @_inject_mpl_docs
    def imshow(self, *args, **kwargs) -> Axes:
        self.ax.imshow(*args, **kwargs)
        self.draw()
        return self.ax

    @_inject_mpl_docs
    def legend(self, *args, **kwargs) -> Legend:
        leg = self.ax.legend(*args, **kwargs)
        self.draw()
        return leg

    @_inject_mpl_docs
    def title(self, *args, **kwargs) -> Text:
        title = self.ax.set_title(*args, **kwargs)
        self.draw()
        return title

    @_inject_mpl_docs
    def xlabel(self, *args, **kwargs) -> None:
        self.ax.set_xlabel(*args, **kwargs)
        self.draw()
        return None

    @_inject_mpl_docs
    def ylabel(self, *args, **kwargs) -> None:
        self.ax.set_ylabel(*args, **kwargs)
        self.draw()
        return None

    @_inject_mpl_docs
    def xticks(self, ticks=None, labels=None, **kwargs) -> tuple[ArrayLike, list[Text]]:
        if ticks is None:
            locs = self.ax.get_xticks()
            if labels is not None:
                raise TypeError(
                    "xticks(): Parameter 'labels' can't be set "
                    "without setting 'ticks'"
                )
        else:
            locs = self.ax.set_xticks(ticks)

        if labels is None:
            labels = self.ax.get_xticklabels()
        else:
            labels = self.ax.set_xticklabels(labels, **kwargs)
        for l in labels:
            l.update(kwargs)
        self.draw()
        return locs, labels

    @_inject_mpl_docs
    def yticks(self, ticks=None, labels=None, **kwargs) -> tuple[ArrayLike, list[Text]]:
        if ticks is None:
            locs = self.ax.get_yticks()
            if labels is not None:
                raise TypeError(
                    "xticks(): Parameter 'labels' can't be set "
                    "without setting 'ticks'"
                )
        else:
            locs = self.ax.set_yticks(ticks)

        if labels is None:
            labels = self.ax.get_yticklabels()
        else:
            labels = self.ax.set_yticklabels(labels, **kwargs)
        for l in labels:
            l.update(kwargs)
        self.draw()
        return locs, labels

    @_inject_mpl_docs
    def twinx(self) -> Axes:
        return self.ax.twinx()

    @_inject_mpl_docs
    def twiny(self) -> Axes:
        return self.ax.twiny()

    @_inject_mpl_docs
    def box(self, on=None) -> None:
        if on is None:
            on = not self.ax.get_frame_on()
        self.ax.set_frame_on(on)
        return None

    @_inject_mpl_docs
    def xscale(self, scale=None) -> None:
        self.ax.set_xscale(scale)
        self.draw()
        return None

    @_inject_mpl_docs
    def yscale(self, scale=None) -> None:
        self.ax.set_yscale(scale)
        self.draw()
        return None

    @_inject_mpl_docs
    def autoscale(self, enable=True, axis="both", tight=None) -> None:
        self.ax.autoscale(enable=enable, axis=axis, tight=tight)
        self.draw()
        return None


class SeabornFigure(Figure):
    """A matplotlib figure canvas implemented with seaborn plot functions."""

    def __init__(
        self,
        nrows: int = 1,
        ncols: int = 1,
        figsize: tuple[float, float] = (4.0, 3.0),
        style=None,
        **kwargs,
    ):
        super().__init__(**locals())
        import seaborn as sns

        self._seaborn = sns

    def swarmplot(self, **kwargs):
        return self._seaborn.swarmplot(ax=self.ax, **kwargs)

    def barplot(self, **kwargs):
        return self._seaborn.barplot(ax=self.ax, **kwargs)

    def boxplot(self, **kwargs):
        return self._seaborn.boxplot(ax=self.ax, **kwargs)

    def boxenplot(self, **kwargs):
        return self._seaborn.boxenplot(ax=self.ax, **kwargs)

    def violinplot(self, **kwargs):
        return self._seaborn.violinplot(ax=self.ax, **kwargs)

    def pairplot(self, **kwargs):
        return self._seaborn.pairplot(ax=self.ax, **kwargs)

    def barplot(self, **kwargs):
        return self._seaborn.barplot(ax=self.ax, **kwargs)

    def pointplot(self, **kwargs):
        return self._seaborn.pointplot(ax=self.ax, **kwargs)
