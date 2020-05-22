from py_pdf_parser.common import BoundingBox
from py_pdf_parser.exceptions import (
    InvalidTableError,
    InvalidTableHeaderError,
    TableExtractionError,
)
from py_pdf_parser.tables import (
    extract_simple_table,
    extract_table,
    get_text_from_table,
    _validate_table_shape,
    add_header_to_table,
    _are_elements_equal,
)

from .base import BaseTestCase
from .utils import create_pdf_document, create_pdf_element, FakePDFMinerTextElement


class TestTables(BaseTestCase):
    def test_extract_simple_table(self):
        # Checks that simple 2*2 table is correctly extracted
        #
        #       elem_1      elem_2
        #       elem_3      elem_4
        #
        elem_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 5))

        document = create_pdf_document(elements=[elem_1, elem_2, elem_3, elem_4])
        elem_list = document.elements

        result = extract_simple_table(elem_list)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assert_original_element_list_list_equal(
            [[elem_1, elem_2], [elem_3, elem_4]], result
        )
        # Checks that it raises an exception when table is not rectangular i.e table
        # has empty cells
        #
        #       elem_1      elem_2
        #       elem_3      elem_4      elem_5
        #
        elem_5 = FakePDFMinerTextElement(bounding_box=BoundingBox(11, 15, 0, 5))

        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4, elem_5]
        )
        elem_list = document.elements
        with self.assertRaises(TableExtractionError):
            extract_simple_table(elem_list)

    def test_extract_simple_table_with_gaps(self):
        #       elem_1      elem_2      elem_3
        #       elem_4      elem_5
        elem_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(11, 15, 6, 10))
        elem_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_5 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 5))
        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4, elem_5]
        )
        elem_list = document.elements
        result = extract_simple_table(elem_list, allow_gaps=True)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 3)
        self.assertEqual(len(result[1]), 3)
        self.assert_original_element_list_list_equal(
            [[elem_1, elem_2, elem_3], [elem_4, elem_5, None]], result
        )

    def test_extract_simple_table_with_gaps_and_different_reference(self):
        #       elem_1      elem_2      elem_3
        #       elem_4      elem_5
        elem_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(11, 15, 6, 10))
        elem_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_5 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 5))
        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4, elem_5]
        )
        elem_list = document.elements
        reference_element = self.extract_element_from_list(elem_2, elem_list)
        result = extract_simple_table(
            elem_list, allow_gaps=True, reference_element=reference_element
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 3)
        self.assertEqual(len(result[1]), 3)
        self.assert_original_element_list_list_equal(
            [[elem_1, elem_2, elem_3], [elem_4, elem_5, None]], result
        )

    def test_extract_simple_table_with_gaps_and_wrong_reference(self):
        #       elem_1      elem_2      elem_3
        #       elem_4      elem_5
        elem_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(11, 15, 6, 10))
        elem_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_5 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 5))
        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4, elem_5]
        )
        elem_list = document.elements
        reference_element = self.extract_element_from_list(elem_3, elem_list)
        with self.assertRaises(TableExtractionError):
            extract_simple_table(
                elem_list, allow_gaps=True, reference_element=reference_element
            )

    def test_extract_simple_table_from_different_pages(self):
        # Checks that simple 2*2 tables are correctly extracted from different pages
        #
        # Page 1:
        #       elem_p1_1      elem_p1_2
        #       elem_p1_3      elem_p1_4
        #
        # Page 2:
        #       elem_p2_1      elem_p2_2
        #       elem_p2_3      elem_p2_4
        #
        elem_p1_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_p1_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_p1_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_p1_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 5))

        elem_p2_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_p2_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_p2_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_p2_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 5))

        document = create_pdf_document(
            elements={
                1: [elem_p1_1, elem_p1_2, elem_p1_3, elem_p1_4],
                2: [elem_p2_1, elem_p2_2, elem_p2_3, elem_p2_4],
            }
        )
        elem_list = document.elements

        result = extract_simple_table(elem_list)
        self.assertEqual(len(result), 4)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assertEqual(len(result[2]), 2)
        self.assertEqual(len(result[3]), 2)
        self.assert_original_element_list_list_equal(
            [
                [elem_p1_1, elem_p1_2],
                [elem_p1_3, elem_p1_4],
                [elem_p2_1, elem_p2_2],
                [elem_p2_3, elem_p2_4],
            ],
            result,
        )

    def test_extract_simple_table_with_tolerance(self):
        # Checks that simple 2*2 table is correctly extracted
        #
        #       elem_1      elem_2
        #       elem_3      elem_4
        # But with elem_4 slightly overlapping elem_2, counteracted by setting tolerance
        elem_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 6.1))

        document = create_pdf_document(elements=[elem_1, elem_2, elem_3, elem_4])
        elem_list = document.elements

        with self.assertRaises(TableExtractionError):
            extract_simple_table(elem_list)

        result = extract_simple_table(elem_list, tolerance=0.2)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assert_original_element_list_list_equal(
            [[elem_1, elem_2], [elem_3, elem_4]], result
        )

    def test_extract_simple_table_removing_duplicate_header_rows(self):
        #    header_elem_1    header_elem_2
        header_elem_1 = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(0, 5, 21, 25),
        )
        header_elem_2 = FakePDFMinerTextElement(
            text="header 2",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(6, 10, 21, 25),
        )
        document = create_pdf_document(elements=[header_elem_1, header_elem_2])
        elem_list = document.elements

        result = extract_simple_table(elem_list, remove_duplicate_header_rows=True)
        # Extraction here should just return the whole table as it is not possible to
        # have duplicates of a single lined table.
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 2)
        self.assert_original_element_list_list_equal(
            [[header_elem_1, header_elem_2]], result
        )

        #    header_elem_1    header_elem_2
        #       elem_1           elem_2
        #    header_elem_3    header_elem_4
        #       elem_3           elem_4
        #    header_elem_5    header_elem_6
        #
        elem_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 16, 20))
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 16, 20))
        header_elem_3 = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(0, 5, 11, 15),
        )
        header_elem_4 = FakePDFMinerTextElement(
            text="header 2",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(6, 10, 11, 15),
        )
        elem_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        header_elem_5 = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(0, 5, 0, 5),
        )
        header_elem_6 = FakePDFMinerTextElement(
            text="header 2",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(6, 10, 0, 5),
        )

        document = create_pdf_document(
            elements=[
                header_elem_1,
                header_elem_2,
                elem_1,
                elem_2,
                header_elem_3,
                header_elem_4,
                elem_3,
                elem_4,
                header_elem_5,
                header_elem_6,
            ]
        )
        elem_list = document.elements

        result = extract_simple_table(elem_list, remove_duplicate_header_rows=True)
        self.assertEqual(len(result), 3)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assertEqual(len(result[2]), 2)
        self.assert_original_element_list_list_equal(
            [[header_elem_1, header_elem_2], [elem_1, elem_2], [elem_3, elem_4]], result
        )

    def test_extract_simple_table_removing_duplicate_header_different_fonts_or_text(
        self,
    ):
        #    header_elem_1                     header_elem_2
        #    header_elem_3_different_font      header_elem_4
        #    header_elem_5_different_text      header_elem_6
        #
        header_elem_1 = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(0, 5, 21, 25),
        )
        header_elem_2 = FakePDFMinerTextElement(
            text="header 2",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(11, 15, 21, 25),
        )
        header_elem_3_different_font = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=12,
            bounding_box=BoundingBox(0, 5, 16, 20),
        )
        header_elem_4 = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(11, 15, 16, 20),
        )
        header_elem_5_different_text = FakePDFMinerTextElement(
            text="header with a different name",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(0, 5, 11, 15),
        )
        header_elem_6 = FakePDFMinerTextElement(
            text="header 2",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(11, 15, 11, 15),
        )

        document = create_pdf_document(
            elements=[
                header_elem_1,
                header_elem_2,
                header_elem_3_different_font,
                header_elem_4,
                header_elem_5_different_text,
                header_elem_6,
            ]
        )
        elem_list = document.elements

        result = extract_simple_table(elem_list, remove_duplicate_header_rows=True)
        self.assertEqual(len(result), 3)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assertEqual(len(result[2]), 2)
        self.assert_original_element_list_list_equal(
            [
                [header_elem_1, header_elem_2],
                [header_elem_3_different_font, header_elem_4],
                [header_elem_5_different_text, header_elem_6],
            ],
            result,
        )

    def test_extract_table(self):
        # Checks that simple 2*2 table is correctly extracted
        #
        #       elem_1      elem_2
        #       elem_3      elem_4
        #
        elem_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 5))

        document = create_pdf_document(elements=[elem_1, elem_2, elem_3, elem_4])
        elem_list = document.elements

        result = extract_table(elem_list)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assert_original_element_list_list_equal(
            [[elem_1, elem_2], [elem_3, elem_4]], result
        )
        # Checks that the following table is correctly extracted
        #
        #       elem_1      elem_2                  elem_6
        #       elem_3      elem_4      elem_5
        #
        elem_5 = FakePDFMinerTextElement(bounding_box=BoundingBox(11, 15, 0, 5))
        elem_6 = FakePDFMinerTextElement(bounding_box=BoundingBox(16, 20, 6, 10))
        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4, elem_5, elem_6]
        )
        elem_list = document.elements
        result = extract_table(elem_list)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 4)
        self.assertEqual(len(result[1]), 4)
        self.assert_original_element_list_list_equal(
            [[elem_1, elem_2, None, elem_6], [elem_3, elem_4, elem_5, None]], result
        )
        # Checks that it raises an error if one element is in two rows
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(3, 8, 6, 10))
        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4, elem_5, elem_6]
        )
        elem_list = document.elements
        with self.assertRaises(TableExtractionError):
            result = extract_table(elem_list)
        # Checks that it raises an error if one element is in two columns
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 3, 8))
        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4, elem_5, elem_6]
        )
        elem_list = document.elements
        with self.assertRaises(TableExtractionError):
            result = extract_table(elem_list)

    def test_extract_table_from_different_pages(self):
        # Checks that simple 2*2 tables are correctly extracted from different pages
        #
        # Page 1:
        #       elem_p1_1      elem_p1_2
        #       elem_p1_3      elem_p1_4
        #
        # Page 2:
        #       elem_p2_1      elem_p2_2
        #       elem_p2_3      elem_p2_4
        #
        elem_p1_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_p1_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_p1_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_p1_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 5))

        elem_p2_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_p2_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_p2_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_p2_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 5))

        document = create_pdf_document(
            elements={
                1: [elem_p1_1, elem_p1_2, elem_p1_3, elem_p1_4],
                2: [elem_p2_1, elem_p2_2, elem_p2_3, elem_p2_4],
            }
        )
        elem_list = document.elements

        result = extract_table(elem_list)
        self.assertEqual(len(result), 4)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assertEqual(len(result[2]), 2)
        self.assertEqual(len(result[3]), 2)
        self.assert_original_element_list_list_equal(
            [
                [elem_p1_1, elem_p1_2],
                [elem_p1_3, elem_p1_4],
                [elem_p2_1, elem_p2_2],
                [elem_p2_3, elem_p2_4],
            ],
            result,
        )

    def test_extract_table_with_tolerance(self):
        # Checks that simple 2*2 table is correctly extracted
        #
        #       elem_1      elem_2
        #       elem_3      elem_4
        #
        # But with elem_4 slightly overlapping elem_2, counteracted by setting tolerance
        elem_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 6.1))

        document = create_pdf_document(elements=[elem_1, elem_2, elem_3, elem_4])
        elem_list = document.elements

        with self.assertRaises(TableExtractionError):
            extract_table(elem_list)

        result = extract_table(elem_list, tolerance=0.2)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assert_original_element_list_list_equal(
            [[elem_1, elem_2], [elem_3, elem_4]], result
        )

    def test_extract_table_removing_duplicate_header_rows(self):
        #    header_elem_1    header_elem_2
        header_elem_1 = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(0, 5, 21, 25),
        )
        header_elem_2 = FakePDFMinerTextElement(
            text="header 2",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(11, 15, 21, 25),
        )
        document = create_pdf_document(elements=[header_elem_1, header_elem_2])
        elem_list = document.elements

        result = extract_table(elem_list, remove_duplicate_header_rows=True)
        # Extraction here should just return the whole table as it is not possible to
        # have duplicates of a single lined table.
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 2)
        self.assert_original_element_list_list_equal(
            [[header_elem_1, header_elem_2]], result
        )

        #    header_elem_1                     header_elem_2
        #       elem_1           elem_2
        #    header_elem_3                     header_elem_4
        #       elem_3                         elem_4
        #    header_elem_5    header_elem_6
        #
        elem_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 16, 20))
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 16, 20))
        header_elem_3 = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(0, 5, 11, 15),
        )
        header_elem_4 = FakePDFMinerTextElement(
            text="header 2",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(11, 15, 11, 15),
        )
        elem_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(11, 15, 6, 10))
        header_elem_5 = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(0, 5, 0, 5),
        )
        header_elem_6 = FakePDFMinerTextElement(
            text="header 2",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(6, 10, 0, 5),
        )

        document = create_pdf_document(
            elements=[
                header_elem_1,
                header_elem_2,
                elem_1,
                elem_2,
                header_elem_3,
                header_elem_4,
                elem_3,
                elem_4,
                header_elem_5,
                header_elem_6,
            ]
        )
        elem_list = document.elements

        result = extract_table(elem_list, remove_duplicate_header_rows=True)
        # The last row will not be removed as the gaps do not match the header row
        self.assertEqual(len(result), 4)
        self.assertEqual(len(result[0]), 3)
        self.assertEqual(len(result[1]), 3)
        self.assertEqual(len(result[2]), 3)
        self.assertEqual(len(result[3]), 3)
        self.assert_original_element_list_list_equal(
            [
                [header_elem_1, None, header_elem_2],
                [elem_1, elem_2, None],
                [elem_3, None, elem_4],
                [header_elem_5, header_elem_6, None],
            ],
            result,
        )

    def test_extract_table_removing_duplicate_header_different_fonts_or_text(self):
        #    header_elem_1                     header_elem_2
        #    header_elem_3_different_font      header_elem_4
        #    header_elem_5_different_text      header_elem_6
        #
        header_elem_1 = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(0, 5, 21, 25),
        )
        header_elem_2 = FakePDFMinerTextElement(
            text="header 2",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(11, 15, 21, 25),
        )
        header_elem_3_different_font = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=12,
            bounding_box=BoundingBox(0, 5, 16, 20),
        )
        header_elem_4 = FakePDFMinerTextElement(
            text="header 1",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(11, 15, 16, 20),
        )
        header_elem_5_different_text = FakePDFMinerTextElement(
            text="header with a different name",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(0, 5, 11, 15),
        )
        header_elem_6 = FakePDFMinerTextElement(
            text="header 2",
            font_name="header font",
            font_size=10,
            bounding_box=BoundingBox(11, 15, 11, 15),
        )

        document = create_pdf_document(
            elements=[
                header_elem_1,
                header_elem_2,
                header_elem_3_different_font,
                header_elem_4,
                header_elem_5_different_text,
                header_elem_6,
            ]
        )
        elem_list = document.elements

        result = extract_table(elem_list, remove_duplicate_header_rows=True)
        self.assertEqual(len(result), 3)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assertEqual(len(result[2]), 2)
        self.assert_original_element_list_list_equal(
            [
                [header_elem_1, header_elem_2],
                [header_elem_3_different_font, header_elem_4],
                [header_elem_5_different_text, header_elem_6],
            ],
            result,
        )

    def test_extract_text_from_simple_table(self):
        # Checks that text from simple 2*2 table is correctly extracted
        #
        #       elem_1      elem_2
        #       elem_3      elem_4
        #
        elem_1 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(0, 5, 6, 10), text="fake_text_1"
        )
        elem_2 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(6, 10, 6, 10), text="fake_text_2"
        )
        elem_3 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(0, 5, 0, 5), text="fake_text_3"
        )
        elem_4 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(6, 10, 0, 5), text="fake_text_4 "
        )

        document = create_pdf_document(elements=[elem_1, elem_2, elem_3, elem_4])
        elem_list = document.elements

        result = extract_simple_table(elem_list, as_text=True)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)

        self.assertListEqual(
            [["fake_text_1", "fake_text_2"], ["fake_text_3", "fake_text_4"]], result
        )

        result = extract_simple_table(elem_list, as_text=True, strip_text=False)
        self.assertListEqual(
            [["fake_text_1", "fake_text_2"], ["fake_text_3", "fake_text_4 "]], result
        )

    def test_extract_text_from_table(self):
        # Checks that text from 2*2 table is correctly extracted
        #
        #       elem_1      elem_2
        #       elem_3      elem_4
        #
        elem_1 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(0, 5, 6, 10), text="fake_text_1"
        )
        elem_2 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(6, 10, 6, 10), text="fake_text_2"
        )
        elem_3 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(0, 5, 0, 5), text="fake_text_3"
        )
        elem_4 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(6, 10, 0, 5), text="fake_text_4 "
        )

        document = create_pdf_document(elements=[elem_1, elem_2, elem_3, elem_4])
        elem_list = document.elements

        result = extract_table(elem_list, as_text=True)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assertListEqual(
            [["fake_text_1", "fake_text_2"], ["fake_text_3", "fake_text_4"]], result
        )

        result = extract_table(elem_list, as_text=True, strip_text=False)
        self.assertListEqual(
            [["fake_text_1", "fake_text_2"], ["fake_text_3", "fake_text_4 "]], result
        )

        # Checks that text from the following table is correctly extracted
        #
        #       elem_1      elem_2                  elem_6
        #       elem_3      elem_4      elem_5
        #
        elem_5 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(11, 15, 0, 5), text="fake_text_5"
        )
        elem_6 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(16, 20, 6, 10), text="fake_text_6"
        )
        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4, elem_5, elem_6]
        )
        elem_list = document.elements
        result = extract_table(elem_list, as_text=True)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 4)
        self.assertEqual(len(result[1]), 4)
        self.assertListEqual(
            [
                ["fake_text_1", "fake_text_2", "", "fake_text_6"],
                ["fake_text_3", "fake_text_4", "fake_text_5", ""],
            ],
            result,
        )

        result = extract_table(elem_list, as_text=True, strip_text=False)
        self.assertListEqual(
            [
                ["fake_text_1", "fake_text_2", "", "fake_text_6"],
                ["fake_text_3", "fake_text_4 ", "fake_text_5", ""],
            ],
            result,
        )

    def test_add_header_to_table(self):
        # Checks behaviour if header is not provided
        table = []
        result = add_header_to_table(table)
        self.assertEqual(result, [])

        fake_header = ["fake_header_1", "fake_header_2"]
        table = [fake_header]
        result = add_header_to_table(table)
        self.assertEqual(result, [])

        table = [fake_header, ["fake_value_1", "fake_value_2"]]
        result = add_header_to_table(table)
        self.assertEqual(len(result), 1)
        self.assertListEqual(
            result, [{"fake_header_1": "fake_value_1", "fake_header_2": "fake_value_2"}]
        )

        table = [
            fake_header,
            ["fake_value_1.1", "fake_value_1.2"],
            ["fake_value_2.1", "fake_value_2.2"],
        ]
        result = add_header_to_table(table)

        self.assertEqual(len(result), 2)
        self.assertListEqual(
            result,
            [
                {"fake_header_1": "fake_value_1.1", "fake_header_2": "fake_value_1.2"},
                {"fake_header_1": "fake_value_2.1", "fake_header_2": "fake_value_2.2"},
            ],
        )
        # Checks behaviour if header is provided
        fake_header = ["fake_header_1", "fake_header_2"]
        table = []
        result = add_header_to_table(table, header=fake_header)
        self.assertEqual(result, [])

        table = [["fake_value_1", "fake_value_2"]]
        result = add_header_to_table(table, header=fake_header)
        self.assertEqual(len(result), 1)
        self.assertListEqual(
            result, [{"fake_header_1": "fake_value_1", "fake_header_2": "fake_value_2"}]
        )

        table = [
            ["fake_value_1.1", "fake_value_1.2"],
            ["fake_value_2.1", "fake_value_2.2"],
        ]
        result = add_header_to_table(table, header=fake_header)

        self.assertEqual(len(result), 2)
        self.assertListEqual(
            result,
            [
                {"fake_header_1": "fake_value_1.1", "fake_header_2": "fake_value_1.2"},
                {"fake_header_1": "fake_value_2.1", "fake_header_2": "fake_value_2.2"},
            ],
        )

        redundant_fake_header = ["fake_header", "fake_header"]
        with self.assertRaises(InvalidTableHeaderError):
            result = add_header_to_table(table, header=redundant_fake_header)

        too_small_fake_header = ["fake_header"]
        with self.assertRaises(InvalidTableHeaderError):
            result = add_header_to_table(table, header=too_small_fake_header)

    def test_fix_element_in_multiple_rows(self):
        # Checks that the following table is correctly extracted:
        # ---------
        # | 1 | 2 |
        # ----|   |
        # | 3 |   |
        # ---------

        elem_1 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(0, 5, 6, 10), text="fake_text_1"
        )
        elem_2 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(6, 10, 0, 10), text="fake_text_2"
        )
        elem_3 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(0, 5, 0, 5), text="fake_text_3"
        )

        document = create_pdf_document(elements=[elem_1, elem_2, elem_3])
        elem_list = document.elements

        with self.assertRaises(TableExtractionError):
            result = extract_table(elem_list, as_text=True)

        result = extract_table(
            elem_list, as_text=True, fix_element_in_multiple_rows=True
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assertListEqual(
            [["fake_text_1", "fake_text_2"], ["fake_text_3", ""]], result
        )

    def test_fix_element_in_multiple_cols(self):
        # Checks that the following table is correctly extracted:
        # ---------
        # | 1     |
        # --------|
        # | 2 | 3 |
        # ---------

        elem_1 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(0, 10, 6, 10), text="fake_text_1"
        )
        elem_2 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(0, 5, 0, 5), text="fake_text_2"
        )
        elem_3 = FakePDFMinerTextElement(
            bounding_box=BoundingBox(6, 10, 0, 5), text="fake_text_3"
        )

        document = create_pdf_document(elements=[elem_1, elem_2, elem_3])
        elem_list = document.elements

        with self.assertRaises(TableExtractionError):
            result = extract_table(elem_list, as_text=True)

        result = extract_table(
            elem_list, as_text=True, fix_element_in_multiple_cols=True
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 2)
        self.assertListEqual(
            [["fake_text_1", ""], ["fake_text_2", "fake_text_3"]], result
        )

    def test_get_text_from_table(self):
        # Checks that it works with very simple table with one element
        element = create_pdf_element(text=" fake_text ")
        result = get_text_from_table([[element]])
        self.assertEqual(result, [["fake_text"]])

        result = get_text_from_table([[element]], strip_text=False)
        self.assertEqual(result, [[" fake_text "]])

        result = get_text_from_table([[None]])
        self.assertEqual(result, [[""]])
        # Checks that it works with table with multiple rows and columns
        result = get_text_from_table([[element, None], [element, element]])
        self.assertListEqual(result, [["fake_text", ""], ["fake_text", "fake_text"]])

    def test_validate_table_shape(self):
        # Checks that empty table has a valid shape
        table = []
        self.assertIsNone(_validate_table_shape(table))
        # Checks that 2*2 table has a valid shape
        table = [["", ""], ["", ""]]
        self.assertIsNone(_validate_table_shape(table))
        # Checks that 2*2 table containing None has a valid shape
        table = [["", None], ["", ""]]
        self.assertIsNone(_validate_table_shape(table))
        # Checks that non rectangular table does not have a valid shape
        table = [[""], ["", ""]]
        with self.assertRaises(InvalidTableError):
            _validate_table_shape(table)

    def test_are_elements_equal(self):
        self.assertFalse((_are_elements_equal(create_pdf_element(), None)))
        self.assertFalse((_are_elements_equal(None, create_pdf_element())))

        element_1 = create_pdf_element(
            text="fake_text_1", font_name="fake_font", font_size=10
        )
        element_2 = create_pdf_element(
            text="fake_text_2", font_name="fake_font", font_size=10
        )
        self.assertFalse(_are_elements_equal(element_1, element_2))

        element_1 = create_pdf_element(
            text="fake_text", font_name="fake_font_1", font_size=10
        )
        element_2 = create_pdf_element(
            text="fake_text", font_name="fake_font_2", font_size=10
        )
        self.assertFalse(_are_elements_equal(element_1, element_2))

        element_1 = create_pdf_element(
            text="fake_text", font_name="fake_font", font_size=10
        )
        element_2 = create_pdf_element(
            text="fake_text", font_name="fake_font", font_size=12
        )
        self.assertFalse(_are_elements_equal(element_1, element_2))

        self.assertTrue(_are_elements_equal(None, None))

        element_1 = create_pdf_element(
            text="fake_text", font_name="fake_font", font_size=10
        )
        element_2 = create_pdf_element(
            text="fake_text", font_name="fake_font", font_size=10
        )
        self.assertTrue(_are_elements_equal(element_1, element_2))
