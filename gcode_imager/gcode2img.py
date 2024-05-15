from io import BytesIO
import os

from PIL import Image

from .gcode import GCode
from .grapher import Grapher

__all__ = ["gcode2img"]


class gcode2img:
    def __init__(self):
        self.gcode = None

    def gcode2img(self, gcode: GCode | None = None,
                  filename: str | None = None,
                  base_dir: str | None = None,
                  gif: bool = False,
                  frames: int = 30) -> BytesIO:
        if gcode:
            if isinstance(gcode, str):
                self.gcode = GCode(gcode)
            elif isinstance(gcode, GCode):
                self.gcode = gcode
            else:
                raise ValueError("gcode must be a new-line-seperated string or GCode object")
        elif filename:
            base_dir = base_dir or os.getcwd()
            full_path = os.path.join(base_dir, filename)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    self.gcode = GCode(f.read())
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"File {full_path} not found") from exc

        grapher = Grapher(self.gcode)
        output = BytesIO()
        if gif:
            gif_frames: list[Image.Image] = []
            for i in range(frames):
                grapher.trace(percentage=i / frames)
                frame_img = grapher.render()
                gif_frames.append(frame_img.copy())

            gif_frames[0].save(output, format="GIF", save_all=True,
                               append_images=gif_frames[1:], loop=0)
            output.seek(0)
        else:
            grapher.trace()
            img = grapher.render()
            img.save(output, format="PNG")
            output.seek(0)

        return output
