from gcode_imager import gcode2img

from PIL import Image


if __name__ == "__main__":
    imager = gcode2img()
    img_bytes = imager.gcode2img(filename="cube.gcode", gif=True, frames=30)
    img = Image.open(img_bytes)
    img.show()
