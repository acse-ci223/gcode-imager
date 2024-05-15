import plotly.graph_objects as go
from PIL import Image
import numpy as np
import io
import os
from .gcode import GCode

__all__ = ['Grapher']


class Grapher:
    def __init__(self, gcode: GCode):
        self.gcode = gcode
        self.fig = None
        self.dimensions = {"X": 0, "Y": 0, "Z": 0}
        self.absolute_positioning = True

    def trace(self, percentage: float = 1.0):
        # Create a 3D plot
        self.fig = go.Figure()
        self.fig.update_scenes(aspectmode='cube')

        camera = dict(
            up=dict(x=0, y=0, z=1),
            center=dict(x=0, y=0, z=0),
            eye=dict(x=1.5, y=1.5, z=1.25)
        )

        self.fig.update_layout(scene_camera=camera)

        conf = self.gcode.configs()
        dimensions: str = conf.get("printable_area")
        dimensions = dimensions.split(",")[2].strip()
        x, y = dimensions.split("x")
        z = conf.get("printable_height").strip()

        self.dimensions["X"] = float(x)
        self.dimensions["Y"] = float(y)
        self.dimensions["Z"] = float(z)

        self.fig.update_layout(scene=dict(
            xaxis=dict(range=[0, self.dimensions["X"]],
                       showticklabels=False,
                       showgrid=True, zeroline=True),
            yaxis=dict(range=[0, self.dimensions["Y"]],
                       showticklabels=False,
                       showgrid=True, zeroline=True),
            zaxis=dict(range=[0, self.dimensions["Z"]],
                       showticklabels=False,
                       showgrid=True, zeroline=True)
        ))

        self.fig.update_layout(
            paper_bgcolor='rgb(115, 115, 115)',
            scene=dict(
                xaxis=dict(
                    backgroundcolor="rgb(185, 185, 185)",
                    gridcolor="black",
                    showbackground=True,
                    zerolinecolor="black",),
                yaxis=dict(
                    backgroundcolor="rgb(185, 185, 185)",
                    gridcolor="black",
                    showbackground=True,
                    zerolinecolor="white"),
                zaxis=dict(
                    backgroundcolor="rgb(185, 185, 185)",
                    gridcolor="black",
                    showbackground=True,
                    zerolinecolor="black",),),
            margin=dict(
                r=10, l=10,
                b=10, t=10))

        # Read G-code and create line traces for each move command of type G
        x_coords = []
        y_coords = []
        z_coords = []

        current_position = {'X': 0, 'Y': 0, 'Z': 0}

        g_moves = self.gcode.moves()

        # get percentage of moves
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

        # Add line traces to the plot
        self.fig.add_trace(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='lines',
            line=dict(color='red', width=4),
        ))

    def render(self) -> Image.Image:
        if self.fig is None:
            raise RuntimeError("You need to call trace() before render().")

        # Save the plot to a bytes buffer
        buf = io.BytesIO()
        self.fig.write_image(buf, format='png', scale=1, width=300, height=300)
        buf.seek(0)

        # Create a PIL image from the bytes buffer
        image = Image.open(buf)
        return image
