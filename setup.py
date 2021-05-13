import os
import sys
from setuptools import setup, find_packages


if sys.version_info < (3, 6):
    print(sys.stderr, "{}: need Python 3.6 or later.".format(sys.argv[0]))
    print(sys.stderr, "Your Python is {}".format(sys.version))
    sys.exit(1)


ROOT_DIR = os.path.dirname(__file__)


setup(
    name="py-pdf-parser",
    packages=find_packages(),
    exclude=["tests.*", "tests", "docs", "docs.*"],
    version="0.8.0",
    url="https://github.com/jstockwin/py-pdf-parser",
    license="BSD",
    description="A tool to help extracting information from structured PDFs.",
    long_description=open(os.path.join(ROOT_DIR, "README.md")).read(),
    long_description_content_type="text/markdown",
    author="Jake Stockwin",
    author_email="jstockwin@gmail.com",
    include_package_data=True,
    install_requires=[
        "pdfminer.six==20201018",
        "docopt==0.6.2",
        "wand==0.6.6",
        "PyYAML==5.4.1",
    ],
    extras_require={
        "dev": [
            "matplotlib==3.4.2",
            "pillow==8.1.1",
            "pyqt5==5.15.4",
            "pyvoronoi==1.0.5",
            "shapely==1.7.1",
        ],
        "test": [
            "black==21.5b1",
            "ddt==1.4.2",
            "matplotlib==3.4.2",
            "mock==4.0.3",
            "mypy==0.812",
            "nose==1.3.7",
            "pillow==8.1.1",
            "pycodestyle==2.7.0",
            "pyqt5==5.15.4",
            "pytype==2021.5.11",
            "recommonmark==0.7.1",
            "sphinx-autobuild==2021.3.14",
            "sphinx-rtd-theme==0.5.2",
            "Sphinx==4.0.1",
            # This is a sub-dependency but is pinned because the next version doesn't
            # install correctly. See:
            # https://github.com/scikit-build/ninja-python-distributions/issues/27
            "ninja==1.10.0.post2",
        ],
    },
)
