class GCodeParser:
    def __init__(self, gcode):
        self.gcode = gcode

    def parse(self):
        # Parse the GCode
        return self.gcode.split("\n")
