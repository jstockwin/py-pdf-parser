import os

from py_pdf_parser import tables
from py_pdf_parser.exceptions import TableExtractionError
from py_pdf_parser.loaders import load_file

from tests.base import BaseTestCase


class TestSimpleMemo(BaseTestCase):
    def test_output_is_correct(self):
        file_path = os.path.join(
            os.path.dirname(__file__), "../../docs/source/example_files/tables.pdf"
        )

        # Step 1 - Load the file
        FONT_MAPPING = {
            "BAAAAA+LiberationSerif-Bold,12.0": "header",
            "CAAAAA+LiberationSerif,12.0": "table_element",
        }
        document = load_file(file_path, font_mapping=FONT_MAPPING)

        headers = document.elements.filter_by_font("header")

        # Extract reference elements
        simple_table_header = headers.filter_by_text_equal(
            "Simple Table"
        ).extract_single_element()

        simple_table_with_gaps_header = headers.filter_by_text_equal(
            "Simple Table with gaps"
        ).extract_single_element()

        simple_table_with_gaps_in_first_row_col_header = headers.filter_by_text_equal(
            "Simple Table with gaps in first row/col"
        ).extract_single_element()

        non_simple_table_header = headers.filter_by_text_equal(
            "Non Simple Table"
        ).extract_single_element()

        non_simple_table_with_merged_cols_header = headers.filter_by_text_equal(
            "Non Simple Table with Merged Columns"
        ).extract_single_element()

        non_simple_table_with_merged_rows_header = headers.filter_by_text_equal(
            "Non Simple Table with Merged Rows and Columns"
        ).extract_single_element()

        over_the_page_header = headers.filter_by_text_equal(
            "Over the page"
        ).extract_single_element()

        # Extract table elements
        simple_table_elements = document.elements.between(
            simple_table_header, simple_table_with_gaps_header
        )
        simple_table_with_gaps_elements = document.elements.between(
            simple_table_with_gaps_header,
            simple_table_with_gaps_in_first_row_col_header,
        )

        simple_table_with_gaps_in_first_row_col_elements = document.elements.between(
            simple_table_with_gaps_in_first_row_col_header, non_simple_table_header
        )

        non_simple_table_elements = document.elements.between(
            non_simple_table_header, non_simple_table_with_merged_cols_header
        )

        non_simple_table_with_merged_cols_elements = document.elements.between(
            non_simple_table_with_merged_cols_header,
            non_simple_table_with_merged_rows_header,
        )

        non_simple_table_with_merged_rows_and_cols_elements = document.elements.between(
            non_simple_table_with_merged_rows_header, over_the_page_header
        )

        over_the_page_elements = document.elements.after(over_the_page_header)

        # Simple Table
        table = tables.extract_simple_table(simple_table_elements, as_text=True)
        self.assertListEqual(
            table,
            [
                ["Heading 1", "Heading 2", "Heading 3", "Heading 4"],
                ["A", "1", "A", "1"],
                ["B", "2", "B", "2"],
                ["C", "3", "C", "3"],
            ],
        )

        # Simple Table with gaps

        with self.assertRaises(TableExtractionError):
            tables.extract_simple_table(simple_table_with_gaps_elements, as_text=True)

        table = tables.extract_simple_table(
            simple_table_with_gaps_elements, as_text=True, allow_gaps=True
        )
        self.assertListEqual(
            table,
            [
                ["Heading 1", "Heading 2", "Heading 3", "Heading 4"],
                ["A", "1", "", "1"],
                ["B", "", "", ""],
                ["C", "", "C", "3"],
            ],
        )

        # Simple Table with gaps in first row/col
        with self.assertRaises(TableExtractionError):
            tables.extract_simple_table(
                simple_table_with_gaps_in_first_row_col_elements,
                as_text=True,
                allow_gaps=True,
            )

        reference_element = simple_table_with_gaps_in_first_row_col_elements[9]
        table = tables.extract_simple_table(
            simple_table_with_gaps_in_first_row_col_elements,
            as_text=True,
            allow_gaps=True,
            reference_element=reference_element,
        )
        self.assertListEqual(
            table,
            [
                ["Heading 1", "Heading 2", "", "Heading 4"],
                ["", "1", "A", ""],
                ["B", "2", "", "2"],
                ["C", "3", "C", "3"],
            ],
        )

        # Non Simple Table
        table = tables.extract_table(non_simple_table_elements, as_text=True)
        self.assertListEqual(
            table,
            [
                ["", "Heading 2", "Heading 3", "Heading 4"],
                ["A", "1", "", "1"],
                ["B", "", "B", "2"],
                ["C", "3", "C", ""],
            ],
        )

        # Non Simple Table with Merged Columns
        with self.assertRaises(TableExtractionError):
            tables.extract_table(
                non_simple_table_with_merged_cols_elements, as_text=True
            )

        table = tables.extract_table(
            non_simple_table_with_merged_cols_elements,
            as_text=True,
            fix_element_in_multiple_cols=True,
        )
        self.assertListEqual(
            table,
            [
                ["Heading 1", "Heading 2", "Heading 3", "Heading 4"],
                ["A", "1", "A", "1"],
                ["This text spans across multiple columns", "", "B", "2"],
                ["C", "3", "C", "3"],
            ],
        )

        # Non Simple Table with Merged Rows and Columns
        table = tables.extract_table(
            non_simple_table_with_merged_rows_and_cols_elements,
            as_text=True,
            fix_element_in_multiple_rows=True,
            fix_element_in_multiple_cols=True,
        )
        self.assertListEqual(
            table,
            [
                ["Heading 1", "Heading 2", "Heading 3", "Heading 4"],
                [
                    "This text spans across multiple rows and \nmultiple columns.",
                    "",
                    "A",
                    "1",
                ],
                ["", "", "B", "2"],
                ["C", "3", "C", "3"],
            ],
        )

        # Over the page
        table = tables.extract_simple_table(over_the_page_elements, as_text=True)
        self.assertListEqual(
            table,
            [
                ["Heading 1", "Heading 2", "Heading 3", "Heading 4"],
                ["A", "1", "A", "1"],
                ["B", "2", "B", "2"],
                ["C", "3", "C", "3"],
            ],
        )
