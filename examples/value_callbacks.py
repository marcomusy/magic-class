from magicclass import magicclass, field
from magicclass.widgets import Figure
import numpy as np

options = {"widget_type": "FloatSlider", "min": 0.2, "max": 10}

@magicclass
class Plot:
    @magicclass(layout="horizontal")
    class parameters:
        a:int = field(options=options)
        b:int = field(options=options)
    canvas = field(Figure)
    
    @parameters.a.connect
    @parameters.b.connect
    def _plot(self, event=None):
        a = self.parameters.a.value
        b = self.parameters.b.value
        t = np.linspace(0, 4*np.pi, 200)
        self.canvas.ax.cla()
        self.canvas.ax.plot(np.sin(a*t), np.sin(b*t))
        self.canvas.draw()

if __name__ == "__main__":
    m = Plot()
    m.show()