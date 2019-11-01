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
    url="https://github.com/optimor/py-pdf-parser",
    license="BSD",
    description="Tool for pdf parsing",
    author="Jake Stockwin",
    author_email="devteam@billmonitor.com",
    install_requires=[
        "pdfminer.six==20191020",
        "docopt==0.6.2",
        "wand==0.4.4",
        "PyYAML==5.1",
    ],
)
