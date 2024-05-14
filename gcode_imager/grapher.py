from matplotlib import pyplot as plt
from PIL import Image

from .gcode import GCode

__all__ = ['Grapher']


class Grapher:
    def __init__(self, gcode: GCode):
        self.gcode = gcode

    def trace(self):
        pass

    def render(self) -> Image.Image:
        return Image.new("RGB", (640, 400), (255, 255, 255))
