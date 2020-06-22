import os

from py_pdf_parser.components import ElementOrdering
from py_pdf_parser.loaders import load_file

from tests.base import BaseTestCase


class TestSimpleMemo(BaseTestCase):
    def test_output_is_correct(self):
        file_path = os.path.join(
            os.path.dirname(__file__), "../../docs/source/example_files/grid.pdf"
        )

        # Default - left to right, top to bottom
        document = load_file(file_path)
        self.assertListEqual(
            [element.text() for element in document.elements],
            ["Top Left", "Top Right", "Bottom Left", "Bottom Right"],
        )

        # Preset - right to left, top to bottom
        document = load_file(
            file_path, element_ordering=ElementOrdering.RIGHT_TO_LEFT_TOP_TO_BOTTOM
        )
        self.assertListEqual(
            [element.text() for element in document.elements],
            ["Top Right", "Top Left", "Bottom Right", "Bottom Left"],
        )

        # Preset - top to bottom, left to right
        document = load_file(
            file_path, element_ordering=ElementOrdering.TOP_TO_BOTTOM_LEFT_TO_RIGHT
        )
        self.assertListEqual(
            [element.text() for element in document.elements],
            ["Bottom Left", "Top Left", "Bottom Right", "Top Right"],
        )

        # Preset - top to bottom, right to left
        document = load_file(
            file_path, element_ordering=ElementOrdering.TOP_TO_BOTTOM_RIGHT_TO_LEFT
        )
        self.assertListEqual(
            [element.text() for element in document.elements],
            ["Top Right", "Bottom Right", "Top Left", "Bottom Left"],
        )

        # Custom - bottom to top, left to right
        def ordering_function(elements):
            return sorted(elements, key=lambda elem: (elem.x0, elem.y0))

        document = load_file(file_path, element_ordering=ordering_function)
        self.assertListEqual(
            [element.text() for element in document.elements],
            ["Bottom Left", "Top Left", "Bottom Right", "Top Right"],
        )

        # Custom - This PDF has columns!
        # TODO: CHANGE PATH!
        file_path = os.path.join(
            os.path.dirname(__file__), "../../docs/source/example_files/columns.pdf"
        )

        # Default - left to right, top to bottom
        document = load_file(file_path)
        self.assertListEqual(
            [element.text() for element in document.elements],
            [
                "Column 1 Title",
                "Column 2 Title",
                "Here is some column 1 text.",
                "Here is some column 2 text.",
                "Col 1 left",
                "Col 1 right",
                "Col 2 left",
                "Col 2 right",
            ],
        )

        # Visualise, and we can see that the middle is at around x = 300.
        # visualise(document)

        def column_ordering_function(elements):
            return sorted(elements, key=lambda elem: (elem.x0 > 300, -elem.y0, elem.x0))

        document = load_file(file_path, element_ordering=column_ordering_function)
        self.assertListEqual(
            [element.text() for element in document.elements],
            [
                "Column 1 Title",
                "Here is some column 1 text.",
                "Col 1 left",
                "Col 1 right",
                "Column 2 Title",
                "Here is some column 2 text.",
                "Col 2 left",
                "Col 2 right",
            ],
        )
