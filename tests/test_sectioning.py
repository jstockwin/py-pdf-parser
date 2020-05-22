import types

from py_pdf_parser.exceptions import InvalidSectionError, SectionNotFoundError
from py_pdf_parser.sectioning import Sectioning

from .base import BaseTestCase
from .utils import create_pdf_document, create_section, FakePDFMinerTextElement


class TestSection(BaseTestCase):
    def test_contains(self):
        elem_1 = FakePDFMinerTextElement()
        elem_2 = FakePDFMinerTextElement()
        elem_3 = FakePDFMinerTextElement()
        document = create_pdf_document([elem_1, elem_2, elem_3])

        pdf_elem_1 = self.extract_element_from_list(elem_1, document._element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document._element_list)
        pdf_elem_3 = self.extract_element_from_list(elem_3, document._element_list)

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

        pdf_elem_1 = self.extract_element_from_list(elem_1, document._element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document._element_list)
        pdf_elem_3 = self.extract_element_from_list(elem_3, document._element_list)

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

    def test_exceptions(self):
        elem_1 = FakePDFMinerTextElement()
        elem_2 = FakePDFMinerTextElement()
        document = create_pdf_document([elem_1, elem_2])

        pdf_elem_1 = self.extract_element_from_list(elem_1, document._element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document._element_list)
        with self.assertRaises(InvalidSectionError):
            create_section(document, start_element=pdf_elem_2, end_element=pdf_elem_1)

    def test_len(self):
        elem_1 = FakePDFMinerTextElement()
        elem_2 = FakePDFMinerTextElement()
        elem_3 = FakePDFMinerTextElement()
        document = create_pdf_document([elem_1, elem_2, elem_3])

        pdf_elem_1 = self.extract_element_from_list(elem_1, document._element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document._element_list)
        pdf_elem_3 = self.extract_element_from_list(elem_3, document._element_list)

        section = create_section(
            document,
            name="fake_section",
            start_element=pdf_elem_1,
            end_element=pdf_elem_3,
        )
        self.assertEqual(len(section), 3)

        # Ignoring an element should affect the length of the section.
        pdf_elem_2.ignore()
        self.assertEqual(len(section), 2)

    def test_repr(self):
        elem_1 = FakePDFMinerTextElement()
        elem_2 = FakePDFMinerTextElement()
        document = create_pdf_document([elem_1, elem_2])

        pdf_elem_1 = self.extract_element_from_list(elem_1, document._element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document._element_list)

        section = create_section(
            document,
            name="fake_section",
            unique_name="fake_section_0",
            start_element=pdf_elem_1,
            end_element=pdf_elem_2,
        )

        self.assertEqual(
            repr(section),
            (
                "<Section name: 'fake_section', unique_name: 'fake_section_0', "
                "number of elements: 2>"
            ),
        )

        # Ignoring an element should affect the number of elements of the section.
        pdf_elem_2.ignore()
        self.assertEqual(
            repr(section),
            (
                "<Section name: 'fake_section', unique_name: 'fake_section_0', "
                "number of elements: 1>"
            ),
        )


class TestSectioning(BaseTestCase):
    def test_create_section(self):
        elem_1 = FakePDFMinerTextElement()
        elem_2 = FakePDFMinerTextElement()
        elem_3 = FakePDFMinerTextElement()
        document = create_pdf_document([elem_1, elem_2, elem_3])

        pdf_elem_1 = self.extract_element_from_list(elem_1, document._element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document._element_list)
        pdf_elem_3 = self.extract_element_from_list(elem_3, document._element_list)

        sectioning = Sectioning(document)
        sectioning.create_section(
            "fake_section", start_element=pdf_elem_1, end_element=pdf_elem_2
        )

        section_1 = create_section(
            document,
            unique_name="fake_section_0",
            start_element=pdf_elem_1,
            end_element=pdf_elem_2,
        )
        self.assertEqual(len(sectioning.sections), 1)
        self.assertIn(section_1, sectioning.sections)

        # Checks that section with the same name would have different unique names when
        # added in Sectioning
        section_2 = create_section(
            document,
            unique_name="fake_section_1",
            start_element=pdf_elem_2,
            end_element=pdf_elem_3,
        )
        sectioning.create_section(
            name="fake_section", start_element=pdf_elem_2, end_element=pdf_elem_3
        )
        self.assertEqual(len(sectioning.sections), 2)
        self.assertIn(section_1, sectioning.sections)
        self.assertIn(section_2, sectioning.sections)

        # Test with include_end_element being False
        section_3 = sectioning.create_section(
            name="test",
            start_element=pdf_elem_1,
            end_element=pdf_elem_3,
            include_last_element=False,
        )
        self.assertEqual(len(section_3.elements), 2)
        self.assertIn(pdf_elem_1, section_3.elements)
        self.assertIn(pdf_elem_2, section_3.elements)
        self.assertNotIn(pdf_elem_3, section_3.elements)

        with self.assertRaises(InvalidSectionError):
            sectioning.create_section(
                name="test",
                start_element=pdf_elem_1,
                end_element=pdf_elem_1,
                include_last_element=False,
            )

    def test_get_sections_with_name(self):
        elem_1 = FakePDFMinerTextElement()
        elem_2 = FakePDFMinerTextElement()
        document = create_pdf_document([elem_1, elem_2])

        pdf_elem_1 = self.extract_element_from_list(elem_1, document._element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document._element_list)

        self.assertTrue(
            isinstance(
                document.sectioning.get_sections_with_name("foo"), types.GeneratorType
            )
        )
        self.assertEqual(list(document.sectioning.get_sections_with_name("foo")), [])

        section_1 = document.sectioning.create_section("foo", pdf_elem_1, pdf_elem_2)
        section_2 = document.sectioning.create_section("foo", pdf_elem_1, pdf_elem_2)
        document.sectioning.create_section("bar", pdf_elem_1, pdf_elem_2)

        self.assertTrue(
            isinstance(
                document.sectioning.get_sections_with_name("foo"), types.GeneratorType
            )
        )
        self.assertEqual(
            list(document.sectioning.get_sections_with_name("foo")),
            [section_1, section_2],
        )

    def test_get_section(self):
        elem_1 = FakePDFMinerTextElement()
        elem_2 = FakePDFMinerTextElement()
        document = create_pdf_document([elem_1, elem_2])

        pdf_elem_1 = self.extract_element_from_list(elem_1, document._element_list)
        pdf_elem_2 = self.extract_element_from_list(elem_2, document._element_list)

        with self.assertRaises(SectionNotFoundError):
            document.sectioning.get_section("foo")

        self.assertTrue(
            isinstance(
                document.sectioning.get_sections_with_name("foo"), types.GeneratorType
            )
        )
        self.assertEqual(list(document.sectioning.get_sections_with_name("foo")), [])

        section_1 = document.sectioning.create_section("foo", pdf_elem_1, pdf_elem_2)
        section_2 = document.sectioning.create_section("foo", pdf_elem_1, pdf_elem_2)

        self.assertEqual(document.sectioning.get_section("foo_0"), section_1)
        self.assertEqual(document.sectioning.get_section("foo_1"), section_2)
