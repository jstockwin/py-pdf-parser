import os

from unittest import TestCase

from py_pdf_parser.components import PDFDocument
from py_pdf_parser.loaders import load, load_file


class LoadersTest(TestCase):
    def test_load_file(self):
        file_path = os.path.join(os.path.dirname(__file__), "data", "test.pdf")
        document = load_file(file_path)
        self.assertIsInstance(document, PDFDocument)

    def test_load(self):
        file_path = os.path.join(os.path.dirname(__file__), "data", "test.pdf")
        with open(file_path, "rb") as in_file:
            document = load(in_file)
        self.assertIsInstance(document, PDFDocument)

    def test_load_with_text_in_image(self):
        file_path = os.path.join(os.path.dirname(__file__), "data", "image.pdf")
        with open(file_path, "rb") as in_file:
            document = load(in_file)
        self.assertIsInstance(document, PDFDocument)
        self.assertEqual(len(document.elements), 1)

        with open(file_path, "rb") as in_file:
            document = load(in_file, la_params={"all_texts": True})
        self.assertIsInstance(document, PDFDocument)
        self.assertEqual(len(document.elements), 2)

    def test_load_file_with_text_in_image(self):
        file_path = os.path.join(os.path.dirname(__file__), "data", "image.pdf")
        document = load_file(file_path, la_params={"all_texts": True})
        self.assertIsInstance(document, PDFDocument)
        self.assertEqual(len(document.elements), 2)
