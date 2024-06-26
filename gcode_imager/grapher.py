from functools import cache
import plotly.graph_objects as go
from PIL import Image
import numpy as np
import io
from .gcode import GCode

__all__ = ['Grapher']

class Grapher:
    def __init__(self, gcode: GCode):
        self.gcode = gcode
        self.fig = None
        self.dimensions = {"X": 0, "Y": 0, "Z": 0}
        self.absolute_positioning = True
        self.x_coords = []
        self.y_coords = []
        self.z_coords = []

    def trace(self):
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
        current_position: dict[str, float] = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}

        g_moves = self.gcode.moves()

        self.x_coords = [current_position['X']]
        self.y_coords = [current_position['Y']]
        self.z_coords = [current_position['Z']]

        for move in g_moves:
            if move.number == '0' or move.number == '1':
                # Linear move
                x = float(move.parameters.get('X', current_position['X']))
                y = float(move.parameters.get('Y', current_position['Y']))
                z = float(move.parameters.get('Z', current_position['Z']))

                if not self.absolute_positioning:
                    x += current_position['X']
                    y += current_position['Y']
                    z += current_position['Z']

                self.x_coords.append(x)
                self.y_coords.append(y)
                self.z_coords.append(z)

                current_position['X'] = x
                current_position['Y'] = y
                current_position['Z'] = z

            elif move.number == '2' or move.number == '3':
                # Arc move (clockwise or counterclockwise)
                x_center = float(move.parameters.get('I', 0) + current_position['X'])
                y_center = float(move.parameters.get('J', 0) + current_position['Y'])
                radius = np.sqrt((current_position['X'] - x_center) ** 2 + (current_position['Y'] - y_center) ** 2)
                start_angle = np.arctan2(current_position['Y'] - y_center, current_position['X'] - x_center)
                end_angle = np.arctan2(float(move.parameters.get('Y', current_position['Y'])) - y_center,
                                       float(move.parameters.get('X', current_position['X'])) - x_center)
                num_points = 100
                angles = np.linspace(start_angle, end_angle, num_points)
                arc_x = x_center + radius * np.cos(angles)
                arc_y = y_center + radius * np.sin(angles)
                arc_z = np.linspace(current_position['Z'], float(move.parameters.get('Z', current_position['Z'])), num_points)

                self.x_coords.extend(arc_x)
                self.y_coords.extend(arc_y)
                self.z_coords.extend(arc_z)

                current_position['X'] = arc_x[-1]
                current_position['Y'] = arc_y[-1]
                current_position['Z'] = arc_z[-1]

            elif move.number == '20':
                # Set units to inches
                self.units = 'inches'

            elif move.number == '21':
                # Set units to mm
                self.units = 'mm'

            elif move.number == '28':
                # Move to origin
                self.x_coords.append(0)
                self.y_coords.append(0)
                self.z_coords.append(0)
                current_position = {'X': 0, 'Y': 0, 'Z': 0}

            elif move.number == '90':
                # Absolute positioning
                self.absolute_positioning = True

            elif move.number == '91':
                # Relative positioning
                self.absolute_positioning = False

            elif move.number == '92':
                # Set position
                current_position['X'] = float(move.parameters.get('X', current_position['X']))
                current_position['Y'] = float(move.parameters.get('Y', current_position['Y']))
                current_position['Z'] = float(move.parameters.get('Z', current_position['Z']))

    def render(self, percentage: float = 1.0) -> Image.Image:
        if self.fig is None:
            raise RuntimeError("You need to call trace() before render().")

        # Get the percentage of coordinates to plot
        pct = int(len(self.x_coords) * percentage)
        x_coords = self.x_coords[:pct]
        y_coords = self.y_coords[:pct]
        z_coords = self.z_coords[:pct]

        # Add line traces to the plot
        self.fig.add_trace(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='lines',
            line=dict(color='red', width=0.017),
            showlegend=False
        ))

        # Save the plot to a bytes buffer
        buf = io.BytesIO()
        self.fig.write_image(buf, format='png', scale=3, width=500, height=500)
        buf.seek(0)

        # Create a PIL image from the bytes buffer
        image = Image.open(buf)
        buf.close()
        return image
