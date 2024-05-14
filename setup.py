try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="gcode-imager",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="Create images from GCode files for 3D printing.",
    long_descritpion="""
    Create images from GCode files for 3D printing.
    """,
    url="https://github.com/acse-ci223/gcode-imager",
    author="Chris Ioannidis",
    author_email="chris.ioannidis23@imperial.ac.uk",
    packages=["gcode_imager"]
)