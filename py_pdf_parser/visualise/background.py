import os
import tempfile

import wand.image
import wand.color
from PIL import Image


def get_pdf_background(pdf_file_path: str, page_number: int) -> Image.Image:
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

    return Image.open(output_file_path).transpose(Image.FLIP_TOP_BOTTOM)
