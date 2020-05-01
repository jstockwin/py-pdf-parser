import sys
from setuptools import setup, find_packages


if sys.version_info < (3, 6):
    print(sys.stderr, "{}: need Python 3.6 or later.".format(sys.argv[0]))
    print(sys.stderr, "Your Python is {}".format(sys.version))
    sys.exit(1)

setup(
    name="py-pdf-parser",
    packages=find_packages(),
    exclude=["tests.*", "tests"],
    version="0.0.1",
    url="https://github.com/jstockwin/py-pdf-parser",
    license="BSD",
    description="Tool for pdf parsing",
    author="Jake Stockwin",
    author_email="jstockwin@gmail.com",
    install_requires=[
        "pdfminer.six==20200402",
        "docopt==0.6.2",
        "wand==0.4.4",
        "PyYAML==5.1",
    ],
    extras_require={
        "dev": [
            "matplotlib==3.1.2",
            "pillow==7.0.0",
            "pyqt5==5.14.1",
            "pyvoronoi==1.0.5",
            "shapely==1.7.0",
        ],
        "test": [
            "black==19.10b0",
            "ddt==1.2.2",
            "matplotlib==3.1.2",
            "mock==3.0.5",
            "mypy==0.761",
            "nose==1.3.7",
            "pillow==7.0.0",
            "pycodestyle==2.5.0",
            "pyqt5==5.14.1",
            "pytype==2020.1.8",
            "sphinx-rtd-theme==0.4.3",
            "Sphinx==2.3.1",
            # This is a sub-dependency but is pinned because the next version doesn't
            # install correctly. See:
            # https://github.com/scikit-build/ninja-python-distributions/issues/27
            "ninja==1.9.0",
        ],
    },
)
