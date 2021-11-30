__version__ = "0.5.10dev0"

from .core import magicclass, magicmenu, magiccontext, WidgetType, Parameters, Bound, MagicTemplate
from .wrappers import set_options, click, set_design, do_not_record, bind_key
from .fields import field, vfield
from .gui._base import wraps, defaults
from . import widgets

from magicgui import *