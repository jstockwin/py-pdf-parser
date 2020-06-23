import os

from py_pdf_parser.loaders import load_file
from tests.base import BaseTestCase


class TestExtractingTextFromFigures(BaseTestCase):
    def test_output_is_correct(self):
        file_path = os.path.join(
            os.path.dirname(__file__), "../../docs/source/example_files/figure.pdf"
        )

        # Without all_texts
        document = load_file(file_path)
        self.assertListEqual(
            [element.text() for element in document.elements],
            ["Here is some text outside of an image"],
        )

        document = load_file(file_path, la_params={"all_texts": True})
        self.assertListEqual(
            [element.text() for element in document.elements],
            ["This is some text in an image", "Here is some text outside of an image"],
        )
