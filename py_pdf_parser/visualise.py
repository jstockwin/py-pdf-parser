from typing import Tuple

import os
import tempfile
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

import wand.image
from PIL import Image

from .document import PDFDocument

PLOT_SIZE = 15
PLOT_RATIO = 0.706  # portrait A4

STYLES = {
    "untagged": {"color": "#B2EBF2", "linewidth": 1, "alpha": 0.5},
    "tagged": {"color": "#00ACC1", "linewidth": 1, "alpha": 0.5},
    "ignored": {"color": "#F44336", "linewidth": 1, "alpha": 0.5, "linestyle": ":"},
}


def visualise(document: PDFDocument, page_number: int = 1):
    if not document.pdf_file_path:
        raise Exception("Can only visualise when there is a file path.. sorry")  # TODO

    fig, ax = _initialise_plot()

    # draw PDF image as background
    page_info = document.page_info[page_number]
    background = _output_pdf_screenshot(document.pdf_file_path, page_number)
    img = Image.open(background).transpose(Image.FLIP_TOP_BOTTOM)
    plt.imshow(
        img,
        origin="lower",
        extent=[0, page_info.width, 0, page_info.height],
        interpolation="kaiser",
    )

    for element in document.elements_for_page(page_number):
        style = STYLES["untagged"]
        if element.tags:
            style = STYLES["tagged"]
        elif element.ignore:
            style = STYLES["ignored"]
        bbox = element.bounding_box
        rect = matplotlib.patches.Rectangle(
            (bbox.x0, bbox.y0), bbox.width, bbox.height, **style
        )
        ax.add_patch(rect)

    plt.show()


def _initialise_plot() -> Tuple[Figure, Axes]:
    return plt.subplots(figsize=(PLOT_SIZE, PLOT_SIZE * PLOT_RATIO))


def _output_pdf_screenshot(pdf_file_path, page_number):
    """
    Create a screenshot of this PDF page using Ghostscript, to use as the
    background for the matplotlib chart.
    """
    # Appending e.g. [0] to the filename means it only loads the first page
    path_with_page = pdf_file_path + "[{}]".format(page_number - 1)
    pdf_pages = wand.image.Image(filename=path_with_page, resolution=150)
    page = pdf_pages.sequence[0]

    output_directory = tempfile.mkdtemp()
    output_file_path = os.path.join(output_directory, "screenshot.png")

    with wand.image.Image(page) as image:
        # We need to composite this with a white image as a background,
        # because disabling the alpha channel doesn't work.
        bg_params = {
            "width": image.width,
            "height": image.height,
            "background": wand.color.Color("white"),
        }
        with wand.image.Image(**bg_params) as background:
            background.composite(image, 0, 0)
            background.save(filename=output_file_path)

    return output_file_path
