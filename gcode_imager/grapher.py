from matplotlib import pyplot as plt

__all__ = ['Grapher']


class Grapher:
    def __init__(self, gcode):
        self.gcode = gcode
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('G-Code Toolpath')
        self.ax.set_box_aspect([1, 1, 1])
        self.ax.view_init(elev=45, azim=45)

    def plot(self):
        for line in self.gcode.lines:
            x = [line.start.x, line.end.x]
            y = [line.start.y, line.end.y]
            z = [line.start.z, line.end.z]
            self.ax.plot(x, y, z, color='b')

    def show(self):
        plt.show()

    def image(self, filename):
        self.plot()
        self.save(filename)

    def save(self, filename):
        self.fig.savefig(filename)