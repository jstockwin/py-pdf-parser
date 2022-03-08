import os

from py_pdf_parser.loaders import load_file
from py_pdf_parser.visualise.main import PDFVisualiser

from .base import BaseVisualiseTestCase


class TestVisualise(BaseVisualiseTestCase):
    def test_visualise(self):
        file_path = os.path.join(
            os.path.dirname(__file__), "../docs/source/example_files/tables.pdf"
        )

        FONT_MAPPING = {
            "BAAAAA+LiberationSerif-Bold,12.0": "header",
            "CAAAAA+LiberationSerif,12.0": "table_element",
        }
        document = load_file(file_path, font_mapping=FONT_MAPPING)

        visualiser = PDFVisualiser(
            self.root, document, show_info=True, width=1920, height=1080
        )

        self.check_images(visualiser, "tables1")

        visualiser.toolbar._buttons["Next page"].invoke()
        self.check_images(visualiser, "tables2")
