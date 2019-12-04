from unittest import TestCase


class BaseTestCase(TestCase):
    # Helper functions
    def assert_original_element_in(self, original_element, element_list):
        pdf_element = self.extract_element_from_list(original_element, element_list)
        self.assertIn(pdf_element, element_list)

    def assert_original_element_list_list_equal(
        self, original_element_list_list, element_list_list
    ):
        self.assertEqual(len(original_element_list_list), len(element_list_list))
        for original_element_list, element_list in zip(
            original_element_list_list, element_list_list
        ):
            self.assert_original_element_list_equal(original_element_list, element_list)

    def assert_original_element_list_equal(self, original_element_list, element_list):
        self.assertEqual(len(original_element_list), len(element_list))
        for original_element, element in zip(original_element_list, element_list):
            self.assert_original_element_equal(original_element, element)

    def assert_original_element_equal(self, original_element, element):
        if original_element is None:
            self.assertIsNone(element)
        else:
            self.assertEqual(original_element, element.original_element)

    def extract_element_from_list(self, original_element, element_list):
        return [
            elem
            for elem in element_list
            if elem is not None
            if elem.original_element == original_element
        ][0]
