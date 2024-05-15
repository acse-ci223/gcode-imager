from matplotlib import pyplot as plt
from matplotlib import axes, figure
import matplotlib.patheffects as pe
from PIL import Image
import numpy as np
import io

from .gcode import GCode

__all__ = ['Grapher']


class Grapher:
    def __init__(self, gcode: GCode):
        self.gcode = gcode
        self.fig: figure.Figure | None = None
        self.ax: axes.Axes | None = None
        self.dimensions = {"X": 0, "Y": 0, "Z": 0}

    def trace(self, percentage: float = 1.0):
        # Create a 3D plot
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')

        conf = self.gcode.configs()
        dimentions: str = conf.get("printable_area")
        dimentions = dimentions.split(",")[2].strip()
        x, y = dimentions.split("x")
        z = conf.get("printable_height").strip()

        self.dimensions["X"] = float(x)
        self.dimensions["Y"] = float(y)
        self.dimensions["Z"] = float(z)

        self.ax.set_xlim(0, self.dimensions["X"])
        self.ax.set_ylim(0, self.dimensions["Y"])
        self.ax.set_zlim(0, self.dimensions["Z"])

        # Read G-code and create line traces for each move command of type G
        x_coords = []
        y_coords = []
        z_coords = []

        current_position = {'X': 0, 'Y': 0, 'Z': 0}

        g_moves = self.gcode.moves("G")

        # get percentage of of moves
        total_moves = len(g_moves)
        pct = int(total_moves * percentage)
        g_moves = g_moves[:pct]

        for move in g_moves:
            if move.number == '0' or move.number == '1':
                # Linear move
                x = move.parameters.get('X', current_position['X'])
                y = move.parameters.get('Y', current_position['Y'])
                z = move.parameters.get('Z', current_position['Z'])

                if not self.absolute_positioning:
                    x += current_position['X']
                    y += current_position['Y']
                    z += current_position['Z']

                x_coords.extend([current_position['X'], x])
                y_coords.extend([current_position['Y'], y])
                z_coords.extend([current_position['Z'], z])

                current_position['X'] = x
                current_position['Y'] = y
                current_position['Z'] = z

            elif move.number == '2' or move.number == '3':
                # Arc move (clockwise or counterclockwise)
                # Simplified example, actual arc calculation would be more complex
                x_center = move.parameters.get('I', 0) + current_position['X']
                y_center = move.parameters.get('J', 0) + current_position['Y']
                radius = np.sqrt((current_position['X'] - x_center) ** 2 + (current_position['Y'] - y_center) ** 2)
                start_angle = np.arctan2(current_position['Y'] - y_center, current_position['X'] - x_center)
                end_angle = np.arctan2(move.parameters.get('Y', current_position['Y']) - y_center,
                                        move.parameters.get('X', current_position['X']) - x_center)
                num_points = 100
                angles = np.linspace(start_angle, end_angle, num_points)
                arc_x = x_center + radius * np.cos(angles)
                arc_y = y_center + radius * np.sin(angles)
                arc_z = np.linspace(current_position['Z'], move.parameters.get('Z', current_position['Z']), num_points)

                x_coords.extend(arc_x)
                y_coords.extend(arc_y)
                z_coords.extend(arc_z)

                current_position['X'] = arc_x[-1]
                current_position['Y'] = arc_y[-1]
                current_position['Z'] = arc_z[-1]

            elif move.number == '4':
                # Dwell command, no action needed
                pass

            elif move.number == '20':
                # Set units to inches
                self.units = 'inches'

            elif move.number == '21':
                # Set units to mm
                self.units = 'mm'

            elif move.number == '28':
                # Move to origin
                x_coords.extend([current_position['X'], 0])
                y_coords.extend([current_position['Y'], 0])
                z_coords.extend([current_position['Z'], 0])
                current_position = {'X': 0, 'Y': 0, 'Z': 0}

            elif move.number == '90':
                # Absolute positioning
                self.absolute_positioning = True

            elif move.number == '91':
                # Relative positioning
                self.absolute_positioning = False

            elif move.number == '92':
                # Set position
                current_position['X'] = move.parameters.get('X', current_position['X'])
                current_position['Y'] = move.parameters.get('Y', current_position['Y'])
                current_position['Z'] = move.parameters.get('Z', current_position['Z'])

            elif move.number == '94':
                # Set feedrate, no action needed
                pass

        # Plot the line traces
        self.ax.plot(x_coords, y_coords, z_coords, antialiased=False, color='red',
                     linewidth=1.0, alpha=1.0, zorder=1,
                     path_effects=[pe.SimpleLineShadow(shadow_color='black'), pe.Normal()])
        # self.ax.legend()
        self.ax.set_xlabel('')
        self.ax.set_ylabel('')
        self.ax.set_zlabel('')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_zticks([])
        self.ax.set_aspect('equal')
        self.ax.set_facecolor((0.47, 0.47, 0.47))

        self.ax.view_init(elev=30, azim=45+int(360*percentage))
        # plt.show()

    def render(self) -> Image.Image:
        if self.fig is None:
            raise RuntimeError("You need to call trace() before render().")

        # Save the plot to a bytes buffer
        buf = io.BytesIO()
        self.fig.savefig(buf, format='png',
                         bbox_inches='tight',
                         facecolor='black',
                         dpi=500,
                         edgecolor='black',
                         pad_inches=0,
                         transparent=False)
        buf.seek(0)

        # Create a PIL image from the bytes buffer
        image = Image.open(buf)
        # buf.close()
        plt.close(self.fig)
        return image
