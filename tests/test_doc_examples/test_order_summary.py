import os

from py_pdf_parser import tables
from py_pdf_parser.loaders import load_file

from tests.base import BaseTestCase


class TestSimpleMemo(BaseTestCase):
    def test_output_is_correct(self):
        # The code below should match that in the documentation example "order_summary"
        # Step 1 - Load the document
        file_path = os.path.join(
            os.path.dirname(__file__),
            "../../docs/source/example_files/order_summary.pdf",
        )
        FONT_MAPPING = {
            "BAAAAA+LiberationSerif-Bold,16.0": "title",
            "BAAAAA+LiberationSerif-Bold,12.0": "sub_title",
            "CAAAAA+LiberationSerif,12.0": "text",
            "DAAAAA+FreeMonoBold,12.0": "table_header",
            "EAAAAA+FreeMono,12.0": "table_text",
        }
        document = load_file(file_path, font_mapping=FONT_MAPPING)

        # visualise(document)

        # Step 3 - Add sections
        order_summary_sub_title_element = (
            document.elements.filter_by_font("sub_title")
            .filter_by_text_equal("Order Summary:")
            .extract_single_element()
        )

        totals_sub_title_element = (
            document.elements.filter_by_font("sub_title")
            .filter_by_text_equal("Totals:")
            .extract_single_element()
        )

        final_element = document.elements[-1]

        order_summary_section = document.sectioning.create_section(
            name="order_summary",
            start_element=order_summary_sub_title_element,
            end_element=totals_sub_title_element,
            include_last_element=False,
        )

        totals_section = document.sectioning.create_section(
            name="totals",
            start_element=totals_sub_title_element,
            end_element=final_element,
        )

        # visualise(document)

        # Step 4 - Extract tables

        order_summary_table = tables.extract_simple_table(
            order_summary_section.elements.filter_by_fonts(
                "table_header", "table_text"
            ),
            as_text=True,
        )

        totals_table = tables.extract_simple_table(
            totals_section.elements.filter_by_fonts("table_header", "table_text"),
            as_text=True,
        )

        order_summary_with_header = tables.add_header_to_table(order_summary_table)

        self.assertListEqual(
            order_summary_table,
            [
                ["Item", "Unit Cost", "Quantity", "Cost"],
                ["Challenger 100g\nWhole Hops", "£3.29", "1", "£3.29"],
                [
                    "Maris Otter \nPale Ale Malt \n(Crushed)",
                    "£1.50/1000g",
                    "4000g",
                    "£6.00",
                ],
                ["WLP037 \nYorkshire Ale \nYeast", "£7.08", "1", "£7.08"],
                ["Bottle Caps", "£1 per 100", "500", "£5"],
            ],
        )

        self.assertListEqual(
            totals_table,
            [
                ["Subtotal:", "£26.28"],
                ["Shipping", "£6"],
                ["VAT 20%", "£6.45"],
                ["Total:", "£38.73"],
            ],
        )

        self.assertListEqual(
            order_summary_with_header,
            [
                {
                    "Item": "Challenger 100g\nWhole Hops",
                    "Unit Cost": "£3.29",
                    "Quantity": "1",
                    "Cost": "£3.29",
                },
                {
                    "Item": "Maris Otter \nPale Ale Malt \n(Crushed)",
                    "Unit Cost": "£1.50/1000g",
                    "Quantity": "4000g",
                    "Cost": "£6.00",
                },
                {
                    "Item": "WLP037 \nYorkshire Ale \nYeast",
                    "Unit Cost": "£7.08",
                    "Quantity": "1",
                    "Cost": "£7.08",
                },
                {
                    "Item": "Bottle Caps",
                    "Unit Cost": "£1 per 100",
                    "Quantity": "500",
                    "Cost": "£5",
                },
            ],
        )
