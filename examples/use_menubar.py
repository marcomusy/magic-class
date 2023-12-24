from magicclass import magicclass, magicmenu, set_options, abstractapi, field
from magicgui.widgets import Image
from pathlib import Path
from skimage.io import imread, imsave
from skimage.filters import gaussian, sobel

@magicclass
class Main:
    @magicmenu
    class File:
        Open_image = abstractapi()
        Save_image = abstractapi()

    @magicmenu
    class Filters:
        Gaussian_filter = abstractapi()
        Sobel_filter = abstractapi()

    @File.wraps
    @set_options(path={"filter": "*.png;*.jpeg;*.tif;*.tiff", "mode": "r"})
    def Open_image(self, path: Path):
        """
        Open an image and display.
        """
        self.image.value = imread(path)

    @File.wraps
    @set_options(path={"filter": "*.png;*.jpeg;*.tif;*.tiff", "mode": "w"})
    def Save_image(self, path: Path):
        """
        Save current image.
        """
        imsave(path, self.image.value)

    @Filters.wraps
    def Gaussian_filter(self, sigma: float = 1):
        """
        Apply Gaussian filter.

        Parameters
        ----------
        sigma : float, default is 1.0
            Standar deviation of Gaussian filter.
        """
        out = gaussian(self.image.value, sigma=sigma)
        self.image.value = out

    @Filters.wraps
    def Sobel_filter(self):
        """
        Apply Sobel filter.
        """
        out = sobel(self.image.value)
        self.image.value = out

    image = field(Image)

if __name__ == "__main__":
    ui = Main()
    ui.show(run=True)
