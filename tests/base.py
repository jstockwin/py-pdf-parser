from typing import List, Optional, Union, TYPE_CHECKING

import logging

from unittest import TestCase

if TYPE_CHECKING:
    from pdfminer.layout import LTComponent

    from py_pdf_parser.components import PDFElement
    from py_pdf_parser.filtering import ElementList


# Turn of debug spam from pdfminer
logging.getLogger("pdfminer").setLevel(logging.WARNING)


class BaseTestCase(TestCase):
    # Helper functions
    def assert_original_element_in(
        self, original_element: "LTComponent", element_list: "ElementList"
    ):
        pdf_element = self.extract_element_from_list(original_element, element_list)
        self.assertIn(pdf_element, element_list)

    def assert_original_element_list_list_equal(
        self,
        original_element_list_list: List[List[Optional["LTComponent"]]],
        element_list_list: List[List[Optional["PDFElement"]]],
    ):
        self.assertEqual(len(original_element_list_list), len(element_list_list))
        for original_element_list, element_list in zip(
            original_element_list_list, element_list_list
        ):
            self.assert_original_element_list_equal(original_element_list, element_list)

    def assert_original_element_list_equal(
        self,
        original_element_list: List[Optional["LTComponent"]],
        element_list: Union[List[Optional["PDFElement"]], "ElementList"],
    ):
        self.assertEqual(len(original_element_list), len(element_list))
        for original_element, element in zip(original_element_list, element_list):
            if original_element is None or element is None:
                self.assertIsNone(original_element)
                self.assertIsNone(element)
            else:
                self.assert_original_element_equal(original_element, element)

    def assert_original_element_equal(
        self, original_element: "LTComponent", element: "PDFElement"
    ):
        self.assertEqual(original_element, element.original_element)

    def extract_element_from_list(
        self,
        original_element: "LTComponent",
        element_list: Union[List[Optional["PDFElement"]], "ElementList"],
    ) -> "PDFElement":
        return [
            elem
            for elem in element_list
            if elem is not None
            if elem.original_element == original_element
        ][0]
