import os
import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 6):
    print(sys.stderr, "{}: need Python 3.6 or later.".format(sys.argv[0]))
    print(sys.stderr, "Your Python is {}".format(sys.version))
    sys.exit(1)


ROOT_DIR = os.path.dirname(__file__)


setup(
    name="py-pdf-parser",
    packages=find_packages(),
    exclude=["tests.*", "tests", "docs", "docs.*"],
    version="0.12.0",
    url="https://github.com/jstockwin/py-pdf-parser",
    license="BSD",
    description="A tool to help extracting information from structured PDFs.",
    long_description=open(os.path.join(ROOT_DIR, "README.md")).read(),
    long_description_content_type="text/markdown",
    author="Jake Stockwin",
    author_email="jstockwin@gmail.com",
    include_package_data=True,
    install_requires=[
        "pdfminer.six==20231228",
        "docopt==0.6.2",
        "wand==0.6.10",
    ],
    extras_require={
        "dev": [
            "matplotlib==3.5.1",
            "pillow==9.2.0",
            "pyvoronoi==1.0.7",
            "shapely==1.8.2",
        ],
        "test": [
            "ddt==1.6.0",
            "matplotlib==3.5.1",
            "mock==4.0.3",
            "nose==1.3.7",
            "pillow==9.2.0",
            "recommonmark==0.7.1",
            "sphinx-autobuild==2021.3.14",
            "sphinx-rtd-theme==1.0.0",
            "Sphinx==5.2.3",
        ],
    },
)
