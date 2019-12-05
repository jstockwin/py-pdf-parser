from py_pdf_parser.sectioning import Sectioning
from py_pdf_parser.tests.base import BaseTestCase

from utils import create_pdf_document, create_section, FakePDFMinerTextElement


class TestSection(BaseTestCase):
    def test_contains(self):
        elem_1 = FakePDFMinerTextElement()
        elem_2 = FakePDFMinerTextElement()
        elem_3 = FakePDFMinerTextElement()
        document = create_pdf_document([elem_1, elem_2, elem_3])

        pdf_elem_1 = self.extract_element_from_list(elem_1, document.element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document.element_list)
        pdf_elem_3 = self.extract_element_from_list(elem_3, document.element_list)

        section = create_section(
            document, start_element=pdf_elem_1, end_element=pdf_elem_2
        )

        self.assertIn(pdf_elem_1, section)
        self.assertIn(pdf_elem_2, section)
        self.assertNotIn(pdf_elem_3, section)

    def test_eq(self):
        elem_1 = FakePDFMinerTextElement()
        elem_2 = FakePDFMinerTextElement()
        elem_3 = FakePDFMinerTextElement()
        document = create_pdf_document([elem_1, elem_2, elem_3])

        pdf_elem_1 = self.extract_element_from_list(elem_1, document.element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document.element_list)
        pdf_elem_3 = self.extract_element_from_list(elem_3, document.element_list)

        section_1 = create_section(
            document, start_element=pdf_elem_1, end_element=pdf_elem_2
        )
        section_2 = create_section(
            document, start_element=pdf_elem_1, end_element=pdf_elem_2
        )
        self.assertEqual(section_1, section_2)
        section_3 = create_section(
            document, start_element=pdf_elem_1, end_element=pdf_elem_3
        )
        self.assertNotEqual(section_1, section_3)


class TestSectioning(BaseTestCase):
    def test_create_section(self):
        elem_1 = FakePDFMinerTextElement()
        elem_2 = FakePDFMinerTextElement()
        elem_3 = FakePDFMinerTextElement()
        document = create_pdf_document([elem_1, elem_2, elem_3])

        pdf_elem_1 = self.extract_element_from_list(elem_1, document.element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document.element_list)
        pdf_elem_3 = self.extract_element_from_list(elem_3, document.element_list)

        result = Sectioning(document)
        result.create_section(
            "fake_section", start_element=pdf_elem_1, end_element=pdf_elem_2
        )

        section_1 = create_section(
            document,
            unique_name="fake_section_0",
            start_element=pdf_elem_1,
            end_element=pdf_elem_2,
        )
        self.assertEqual(len(result.sections), 1)
        self.assertIn(section_1, result.sections)

        # Checks that section with the same name would have different unique names when
        # added in Sectioning
        section_2 = create_section(
            document,
            unique_name="fake_section_1",
            start_element=pdf_elem_2,
            end_element=pdf_elem_3,
        )
        result.create_section(
            name="fake_section", start_element=pdf_elem_2, end_element=pdf_elem_3
        )
        self.assertEqual(len(result.sections), 2)
        self.assertIn(section_1, result.sections)
        self.assertIn(section_2, result.sections)
