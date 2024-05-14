from gcode_imager import gcode2img


if __name__ == "__main__":
    imager = gcode2img()
    img = imager.gcode2img(filename="cube.gcode")
    img.show()
