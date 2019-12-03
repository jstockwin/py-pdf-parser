from unittest import TestCase
from mock import patch, call

from py_pdf_parser.components import PDFDocument, PDFElement
from py_pdf_parser.common import BoundingBox
from py_pdf_parser.exceptions import NoElementFoundError, MultipleElementsFoundError
from py_pdf_parser.filtering import ElementList
from py_pdf_parser.loaders import Page
from utils import FakePDFMinerTextElement, create_pdf_document


class TestFiltering(TestCase):
    def setUp(self):
        self.elem1 = FakePDFMinerTextElement()
        self.elem2 = FakePDFMinerTextElement()
        self.elem3 = FakePDFMinerTextElement()
        self.elem4 = FakePDFMinerTextElement()
        self.elem5 = FakePDFMinerTextElement()
        self.elem6 = FakePDFMinerTextElement()
        self.doc = create_pdf_document(
            [self.elem1, self.elem2, self.elem3, self.elem4, self.elem5, self.elem6]
        )
        self.elem_list = self.doc.elements

    def test_filter_by_tag(self):
        self.assertEqual(len(self.elem_list.filter_by_tag("foo")), 0)

        self.elem_list[0].add_tag("foo")
        self.assertEqual(len(self.elem_list.filter_by_tag("foo")), 1)
        self.assertIn(self.elem_list[0], self.elem_list.filter_by_tag("foo"))

        self.elem_list[1].add_tag("bar")
        self.assertEqual(len(self.elem_list.filter_by_tag("foo")), 1)
        self.assertIn(self.elem_list[0], self.elem_list.filter_by_tag("foo"))

        self.elem_list[2].add_tag("foo")
        self.assertEqual(len(self.elem_list.filter_by_tag("foo")), 2)
        self.assertIn(self.elem_list[0], self.elem_list.filter_by_tag("foo"))
        self.assertIn(self.elem_list[2], self.elem_list.filter_by_tag("foo"))

    def test_filter_by_tags(self):
        self.assertEqual(len(self.elem_list.filter_by_tags("foo", "bar")), 0)

        self.elem_list[0].add_tag("foo")
        self.assertEqual(len(self.elem_list.filter_by_tags("foo", "bar")), 1)
        self.assertIn(self.elem_list[0], self.elem_list.filter_by_tags("foo", "bar"))

        self.elem_list[1].add_tag("bar")
        self.assertEqual(len(self.elem_list.filter_by_tags("foo", "bar")), 2)
        self.assertIn(self.elem_list[0], self.elem_list.filter_by_tags("foo", "bar"))
        self.assertIn(self.elem_list[1], self.elem_list.filter_by_tags("foo", "bar"))

        self.elem_list[2].add_tag("foo")
        self.assertEqual(len(self.elem_list.filter_by_tags("foo", "bar")), 3)
        self.assertIn(self.elem_list[0], self.elem_list.filter_by_tags("foo", "bar"))
        self.assertIn(self.elem_list[1], self.elem_list.filter_by_tags("foo", "bar"))
        self.assertIn(self.elem_list[2], self.elem_list.filter_by_tags("foo", "bar"))

        self.elem_list[3].add_tag("baz")
        self.assertEqual(len(self.elem_list.filter_by_tags("foo", "bar")), 3)
        self.assertIn(self.elem_list[0], self.elem_list.filter_by_tags("foo", "bar"))
        self.assertIn(self.elem_list[1], self.elem_list.filter_by_tags("foo", "bar"))
        self.assertIn(self.elem_list[2], self.elem_list.filter_by_tags("foo", "bar"))

    def test_filter_by_text_equal(self):
        elem1 = FakePDFMinerTextElement(text="foo")
        elem2 = FakePDFMinerTextElement(text="bar")
        elem3 = FakePDFMinerTextElement(text="foobar")
        elem4 = FakePDFMinerTextElement(text="baz")
        doc = create_pdf_document([elem1, elem2, elem3, elem4])

        self.assertEqual(len(doc.elements.filter_by_text_equal("hello")), 0)

        self.assertEqual(len(doc.elements.filter_by_text_equal("baz")), 1)
        self.__assert_original_element_in(
            elem4, doc.elements.filter_by_text_equal("baz")
        )

        self.assertEqual(len(doc.elements.filter_by_text_equal("foo")), 1)
        self.__assert_original_element_in(
            elem1, doc.elements.filter_by_text_equal("foo")
        )

    def test_filter_by_text_contains(self):
        elem1 = FakePDFMinerTextElement(text="foo")
        elem2 = FakePDFMinerTextElement(text="bar")
        elem3 = FakePDFMinerTextElement(text="foobar")
        elem4 = FakePDFMinerTextElement(text="baz")
        doc = create_pdf_document([elem1, elem2, elem3, elem4])

        self.assertEqual(len(doc.elements.filter_by_text_contains("hello")), 0)

        self.assertEqual(len(doc.elements.filter_by_text_contains("baz")), 1)
        self.__assert_original_element_in(
            elem4, doc.elements.filter_by_text_contains("baz")
        )

        self.assertEqual(len(doc.elements.filter_by_text_contains("foo")), 2)
        self.__assert_original_element_in(
            elem1, doc.elements.filter_by_text_contains("foo")
        )
        self.__assert_original_element_in(
            elem3, doc.elements.filter_by_text_contains("foo")
        )

    def test_filter_by_font(self):
        elem1 = FakePDFMinerTextElement(font_name="foo", font_size=2)
        elem2 = FakePDFMinerTextElement(font_name="bar", font_size=3)
        doc = create_pdf_document([elem1, elem2])

        self.assertEqual(len(doc.elements.filter_by_font("hello,1")), 0)

        self.assertEqual(len(doc.elements.filter_by_font("foo,2")), 1)
        self.__assert_original_element_in(elem1, doc.elements.filter_by_font("foo,2"))

        doc = create_pdf_document([elem1, elem2], font_mapping={"foo,2": "font_a"})
        self.assertEqual(len(doc.elements.filter_by_font("hello,1")), 0)
        self.assertEqual(len(doc.elements.filter_by_font("foo,2")), 0)

        self.assertEqual(len(doc.elements.filter_by_font("font_a")), 1)
        self.__assert_original_element_in(elem1, doc.elements.filter_by_font("font_a"))

    def test_exclude_ignored(self):
        self.assertEqual(len(self.elem_list.exclude_ignored()), len(self.elem_list))

        self.elem_list[0].ignore = True
        self.assertEqual(len(self.elem_list.exclude_ignored()), len(self.elem_list) - 1)
        self.assertNotIn(self.elem_list[0], self.elem_list.exclude_ignored())

    def test_filter_by_page(self):
        elem1 = FakePDFMinerTextElement()
        elem2 = FakePDFMinerTextElement()
        elem3 = FakePDFMinerTextElement()
        page1 = Page(width=100, height=100, elements=[elem1, elem2])
        page2 = Page(width=100, height=100, elements=[elem3])
        doc = PDFDocument({1: page1, 2: page2})

        self.assertEqual(len(doc.elements.filter_by_page(1)), 2)
        self.__assert_original_element_in(elem1, doc.elements.filter_by_page(1))
        self.__assert_original_element_in(elem2, doc.elements.filter_by_page(1))

    def test_filter_by_pages(self):
        elem1 = FakePDFMinerTextElement()
        elem2 = FakePDFMinerTextElement()
        elem3 = FakePDFMinerTextElement()
        elem4 = FakePDFMinerTextElement()
        page1 = Page(width=100, height=100, elements=[elem1, elem2])
        page2 = Page(width=100, height=100, elements=[elem3])
        page3 = Page(width=100, height=100, elements=[elem4])
        doc = PDFDocument({1: page1, 2: page2, 3: page3})

        self.assertEqual(len(doc.elements.filter_by_pages(1, 2)), 3)
        self.__assert_original_element_in(elem1, doc.elements.filter_by_pages(1, 2))
        self.__assert_original_element_in(elem2, doc.elements.filter_by_pages(1, 2))
        self.__assert_original_element_in(elem3, doc.elements.filter_by_pages(1, 2))

    def test_filter_by_section_name(self):
        self.doc.sectioning.create_section("foo", self.elem_list[0], self.elem_list[1])
        self.assertEqual(len(self.elem_list.filter_by_section_name("foo")), 2)
        self.assertIn(self.elem_list[0], self.elem_list.filter_by_section_name("foo"))
        self.assertIn(self.elem_list[1], self.elem_list.filter_by_section_name("foo"))

        self.doc.sectioning.create_section("foo", self.elem_list[3], self.elem_list[5])
        self.assertEqual(len(self.elem_list.filter_by_section_name("foo")), 5)
        self.assertIn(self.elem_list[0], self.elem_list.filter_by_section_name("foo"))
        self.assertIn(self.elem_list[1], self.elem_list.filter_by_section_name("foo"))
        self.assertIn(self.elem_list[3], self.elem_list.filter_by_section_name("foo"))
        self.assertIn(self.elem_list[4], self.elem_list.filter_by_section_name("foo"))
        self.assertIn(self.elem_list[5], self.elem_list.filter_by_section_name("foo"))

    def test_filter_by_section_names(self):
        self.doc.sectioning.create_section("foo", self.elem_list[0], self.elem_list[1])
        self.doc.sectioning.create_section("bar", self.elem_list[3], self.elem_list[5])

        self.doc.sectioning.create_section("foo", self.elem_list[3], self.elem_list[5])
        self.assertEqual(len(self.elem_list.filter_by_section_names("foo", "bar")), 5)
        self.assertIn(
            self.elem_list[0], self.elem_list.filter_by_section_names("foo", "bar")
        )
        self.assertIn(
            self.elem_list[1], self.elem_list.filter_by_section_names("foo", "bar")
        )
        self.assertIn(
            self.elem_list[3], self.elem_list.filter_by_section_names("foo", "bar")
        )
        self.assertIn(
            self.elem_list[4], self.elem_list.filter_by_section_names("foo", "bar")
        )
        self.assertIn(
            self.elem_list[5], self.elem_list.filter_by_section_names("foo", "bar")
        )

    def test_filter_by_section(self):
        self.doc.sectioning.create_section("foo", self.elem_list[0], self.elem_list[1])
        self.doc.sectioning.create_section("foo", self.elem_list[3], self.elem_list[5])

        self.assertEqual(len(self.elem_list.filter_by_section("foo_0")), 2)
        self.assertIn(self.elem_list[0], self.elem_list.filter_by_section("foo_0"))
        self.assertIn(self.elem_list[1], self.elem_list.filter_by_section("foo_0"))

    def test_filter_by_sections(self):
        self.doc.sectioning.create_section("foo", self.elem_list[0], self.elem_list[1])
        self.doc.sectioning.create_section("foo", self.elem_list[3], self.elem_list[5])

        self.assertEqual(len(self.elem_list.filter_by_sections("foo_0", "foo_1")), 5)
        self.assertIn(
            self.elem_list[0], self.elem_list.filter_by_sections("foo_0", "foo_1")
        )
        self.assertIn(
            self.elem_list[1], self.elem_list.filter_by_sections("foo_0", "foo_1")
        )
        self.assertIn(
            self.elem_list[3], self.elem_list.filter_by_sections("foo_0", "foo_1")
        )
        self.assertIn(
            self.elem_list[4], self.elem_list.filter_by_sections("foo_0", "foo_1")
        )
        self.assertIn(
            self.elem_list[5], self.elem_list.filter_by_sections("foo_0", "foo_1")
        )

    @patch.object(PDFElement, "partially_within", autospec=True)
    def test_to_the_right_of(self, partially_within_mock):
        partially_within_mock.side_effect = (
            lambda self, bounding_box: self.text == "within"
        )

        elem1 = FakePDFMinerTextElement(
            text="within", bounding_box=BoundingBox(50, 51, 50, 51)
        )
        elem2 = FakePDFMinerTextElement(text="within")
        elem3 = FakePDFMinerTextElement()
        elem4 = FakePDFMinerTextElement(text="within")
        elem5 = FakePDFMinerTextElement()
        elem6 = FakePDFMinerTextElement(text="within")

        page1 = Page(elements=[elem1, elem2, elem3, elem4], width=100, height=100)
        page2 = Page(elements=[elem5, elem6], width=100, height=100)

        doc = PDFDocument(pages={1: page1, 2: page2})
        elem_list = doc.elements

        pdf_elem1 = self.__extract_element_from_list(elem1, elem_list)
        pdf_elem2 = self.__extract_element_from_list(elem2, elem_list)
        pdf_elem3 = self.__extract_element_from_list(elem3, elem_list)
        pdf_elem4 = self.__extract_element_from_list(elem4, elem_list)

        result = elem_list.to_the_right_of(pdf_elem1)

        # expected_bbox is from the right edge of elem1 to the right edge of the page
        expected_bbox = BoundingBox(51, 100, 50, 51)
        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem1, expected_bbox),
                call(pdf_elem2, expected_bbox),
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 2)
        self.assertIn(pdf_elem2, result)
        self.assertIn(pdf_elem4, result)

        # Also test with inclusive=True
        partially_within_mock.reset_mock()
        result = elem_list.to_the_right_of(pdf_elem1, inclusive=True)

        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem1, expected_bbox),
                call(pdf_elem2, expected_bbox),
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 3)
        self.assertIn(pdf_elem1, result)
        self.assertIn(pdf_elem2, result)
        self.assertIn(pdf_elem4, result)

    @patch.object(PDFElement, "partially_within", autospec=True)
    def test_to_the_left_of(self, partially_within_mock):
        partially_within_mock.side_effect = (
            lambda self, bounding_box: self.text == "within"
        )

        elem1 = FakePDFMinerTextElement(
            text="within", bounding_box=BoundingBox(50, 51, 50, 51)
        )
        elem2 = FakePDFMinerTextElement(text="within")
        elem3 = FakePDFMinerTextElement()
        elem4 = FakePDFMinerTextElement(text="within")
        elem5 = FakePDFMinerTextElement()
        elem6 = FakePDFMinerTextElement(text="within")

        page1 = Page(elements=[elem1, elem2, elem3, elem4], width=100, height=100)
        page2 = Page(elements=[elem5, elem6], width=100, height=100)

        doc = PDFDocument(pages={1: page1, 2: page2})
        elem_list = doc.elements

        pdf_elem1 = self.__extract_element_from_list(elem1, elem_list)
        pdf_elem2 = self.__extract_element_from_list(elem2, elem_list)
        pdf_elem3 = self.__extract_element_from_list(elem3, elem_list)
        pdf_elem4 = self.__extract_element_from_list(elem4, elem_list)

        result = elem_list.to_the_left_of(pdf_elem1)

        # expected_bbox is from the left edge of elem1 to the left edge of the page
        expected_bbox = BoundingBox(0, 50, 50, 51)
        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem1, expected_bbox),
                call(pdf_elem2, expected_bbox),
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 2)
        self.assertIn(pdf_elem2, result)
        self.assertIn(pdf_elem4, result)

        # Also test with inclusive=True
        partially_within_mock.reset_mock()
        result = elem_list.to_the_left_of(pdf_elem1, inclusive=True)

        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem1, expected_bbox),
                call(pdf_elem2, expected_bbox),
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 3)
        self.assertIn(pdf_elem1, result)
        self.assertIn(pdf_elem2, result)
        self.assertIn(pdf_elem4, result)

    @patch.object(PDFElement, "partially_within", autospec=True)
    def test_below(self, partially_within_mock):
        partially_within_mock.side_effect = (
            lambda self, bounding_box: self.text == "within"
        )

        elem1 = FakePDFMinerTextElement(text="within")
        elem2 = FakePDFMinerTextElement()
        elem3 = FakePDFMinerTextElement(
            text="within", bounding_box=BoundingBox(50, 51, 50, 51)
        )
        elem4 = FakePDFMinerTextElement(text="within")
        elem5 = FakePDFMinerTextElement()
        elem6 = FakePDFMinerTextElement(text="within")
        elem7 = FakePDFMinerTextElement()
        elem8 = FakePDFMinerTextElement(text="within")

        page1 = Page(elements=[elem1, elem2], width=100, height=100)
        page2 = Page(elements=[elem3, elem4, elem5, elem6], width=100, height=100)
        page3 = Page(elements=[elem7, elem8], width=100, height=100)

        doc = PDFDocument(pages={1: page1, 2: page2, 3: page3})
        elem_list = doc.elements

        pdf_elem3 = self.__extract_element_from_list(elem3, elem_list)
        pdf_elem4 = self.__extract_element_from_list(elem4, elem_list)
        pdf_elem5 = self.__extract_element_from_list(elem5, elem_list)
        pdf_elem6 = self.__extract_element_from_list(elem6, elem_list)
        pdf_elem7 = self.__extract_element_from_list(elem7, elem_list)
        pdf_elem8 = self.__extract_element_from_list(elem8, elem_list)

        result = elem_list.below(pdf_elem3)

        # expected_bbox is from the left edge of elem1 to the left edge of the page
        expected_bbox = BoundingBox(50, 51, 0, 50)
        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
                call(pdf_elem5, expected_bbox),
                call(pdf_elem6, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 2)
        self.assertIn(pdf_elem4, result)
        self.assertIn(pdf_elem6, result)

        # Also test with inclusive=True
        partially_within_mock.reset_mock()
        result = elem_list.below(pdf_elem3, inclusive=True)

        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
                call(pdf_elem5, expected_bbox),
                call(pdf_elem6, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 3)
        self.assertIn(pdf_elem3, result)
        self.assertIn(pdf_elem4, result)
        self.assertIn(pdf_elem6, result)

        # Also test with all_pages=True
        partially_within_mock.reset_mock()
        result = elem_list.below(pdf_elem3, all_pages=True)

        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
                call(pdf_elem5, expected_bbox),
                call(pdf_elem6, expected_bbox),
                call(pdf_elem7, BoundingBox(50, 51, 0, 100)),
                call(pdf_elem8, BoundingBox(50, 51, 0, 100)),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 3)
        self.assertIn(pdf_elem4, result)
        self.assertIn(pdf_elem6, result)
        self.assertIn(pdf_elem8, result)

    @patch.object(PDFElement, "partially_within", autospec=True)
    def test_above(self, partially_within_mock):
        partially_within_mock.side_effect = (
            lambda self, bounding_box: self.text == "within"
        )

        elem1 = FakePDFMinerTextElement(text="within")
        elem2 = FakePDFMinerTextElement()
        elem3 = FakePDFMinerTextElement(
            text="within", bounding_box=BoundingBox(50, 51, 50, 51)
        )
        elem4 = FakePDFMinerTextElement(text="within")
        elem5 = FakePDFMinerTextElement()
        elem6 = FakePDFMinerTextElement(text="within")
        elem7 = FakePDFMinerTextElement()
        elem8 = FakePDFMinerTextElement(text="within")

        page1 = Page(elements=[elem1, elem2], width=100, height=100)
        page2 = Page(elements=[elem3, elem4, elem5, elem6], width=100, height=100)
        page3 = Page(elements=[elem7, elem8], width=100, height=100)

        doc = PDFDocument(pages={1: page1, 2: page2, 3: page3})
        elem_list = doc.elements

        pdf_elem1 = self.__extract_element_from_list(elem1, elem_list)
        pdf_elem2 = self.__extract_element_from_list(elem2, elem_list)
        pdf_elem3 = self.__extract_element_from_list(elem3, elem_list)
        pdf_elem4 = self.__extract_element_from_list(elem4, elem_list)
        pdf_elem5 = self.__extract_element_from_list(elem5, elem_list)
        pdf_elem6 = self.__extract_element_from_list(elem6, elem_list)

        result = elem_list.above(pdf_elem3)

        # expected_bbox is from the left edge of elem1 to the left edge of the page
        expected_bbox = BoundingBox(50, 51, 51, 100)
        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
                call(pdf_elem5, expected_bbox),
                call(pdf_elem6, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 2)
        self.assertIn(pdf_elem4, result)
        self.assertIn(pdf_elem6, result)

        # Also test with inclusive=True
        partially_within_mock.reset_mock()
        result = elem_list.above(pdf_elem3, inclusive=True)

        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
                call(pdf_elem5, expected_bbox),
                call(pdf_elem6, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 3)
        self.assertIn(pdf_elem3, result)
        self.assertIn(pdf_elem4, result)
        self.assertIn(pdf_elem6, result)

        # Also test with all_pages=True
        partially_within_mock.reset_mock()
        result = elem_list.above(pdf_elem3, all_pages=True)

        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem1, BoundingBox(50, 51, 0, 100)),
                call(pdf_elem2, BoundingBox(50, 51, 0, 100)),
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
                call(pdf_elem5, expected_bbox),
                call(pdf_elem6, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 3)
        self.assertIn(pdf_elem1, result)
        self.assertIn(pdf_elem4, result)
        self.assertIn(pdf_elem6, result)

    @patch.object(PDFElement, "partially_within", autospec=True)
    def test_vertically_in_line_with(self, partially_within_mock):
        partially_within_mock.side_effect = (
            lambda self, bounding_box: self.text == "within"
        )

        elem1 = FakePDFMinerTextElement(text="within")
        elem2 = FakePDFMinerTextElement()
        elem3 = FakePDFMinerTextElement(
            text="within", bounding_box=BoundingBox(50, 51, 50, 51)
        )
        elem4 = FakePDFMinerTextElement(text="within")
        elem5 = FakePDFMinerTextElement()
        elem6 = FakePDFMinerTextElement(text="within")
        elem7 = FakePDFMinerTextElement()
        elem8 = FakePDFMinerTextElement(text="within")

        page1 = Page(elements=[elem1, elem2], width=100, height=100)
        page2 = Page(elements=[elem3, elem4, elem5, elem6], width=100, height=100)
        page3 = Page(elements=[elem7, elem8], width=100, height=100)

        doc = PDFDocument(pages={1: page1, 2: page2, 3: page3})
        elem_list = doc.elements

        pdf_elem1 = self.__extract_element_from_list(elem1, elem_list)
        pdf_elem2 = self.__extract_element_from_list(elem2, elem_list)
        pdf_elem3 = self.__extract_element_from_list(elem3, elem_list)
        pdf_elem4 = self.__extract_element_from_list(elem4, elem_list)
        pdf_elem5 = self.__extract_element_from_list(elem5, elem_list)
        pdf_elem6 = self.__extract_element_from_list(elem6, elem_list)
        pdf_elem7 = self.__extract_element_from_list(elem7, elem_list)
        pdf_elem8 = self.__extract_element_from_list(elem8, elem_list)

        result = elem_list.vertically_in_line_with(pdf_elem3)

        # expected_bbox is from the left edge of elem1 to the left edge of the page
        expected_bbox = BoundingBox(50, 51, 0, 100)
        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
                call(pdf_elem5, expected_bbox),
                call(pdf_elem6, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 2)
        self.assertIn(pdf_elem4, result)
        self.assertIn(pdf_elem6, result)

        # Also test with inclusive=True
        partially_within_mock.reset_mock()
        result = elem_list.vertically_in_line_with(pdf_elem3, inclusive=True)

        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
                call(pdf_elem5, expected_bbox),
                call(pdf_elem6, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 3)
        self.assertIn(pdf_elem3, result)
        self.assertIn(pdf_elem4, result)
        self.assertIn(pdf_elem6, result)

        # Also test with all_pages=True
        partially_within_mock.reset_mock()
        result = elem_list.vertically_in_line_with(pdf_elem3, all_pages=True)

        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem1, expected_bbox),
                call(pdf_elem2, expected_bbox),
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
                call(pdf_elem5, expected_bbox),
                call(pdf_elem6, expected_bbox),
                call(pdf_elem7, expected_bbox),
                call(pdf_elem8, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 4)
        self.assertIn(pdf_elem1, result)
        self.assertIn(pdf_elem4, result)
        self.assertIn(pdf_elem6, result)
        self.assertIn(pdf_elem8, result)

    @patch.object(PDFElement, "partially_within", autospec=True)
    def test_horizontally_in_line_with(self, partially_within_mock):
        partially_within_mock.side_effect = (
            lambda self, bounding_box: self.text == "within"
        )

        elem1 = FakePDFMinerTextElement(
            text="within", bounding_box=BoundingBox(50, 51, 50, 51)
        )
        elem2 = FakePDFMinerTextElement(text="within")
        elem3 = FakePDFMinerTextElement()
        elem4 = FakePDFMinerTextElement(text="within")
        elem5 = FakePDFMinerTextElement()
        elem6 = FakePDFMinerTextElement(text="within")

        page1 = Page(elements=[elem1, elem2, elem3, elem4], width=100, height=100)
        page2 = Page(elements=[elem5, elem6], width=100, height=100)

        doc = PDFDocument(pages={1: page1, 2: page2})
        elem_list = doc.elements

        pdf_elem1 = self.__extract_element_from_list(elem1, elem_list)
        pdf_elem2 = self.__extract_element_from_list(elem2, elem_list)
        pdf_elem3 = self.__extract_element_from_list(elem3, elem_list)
        pdf_elem4 = self.__extract_element_from_list(elem4, elem_list)

        result = elem_list.horizontally_in_line_with(pdf_elem1)

        # expected_bbox is from the left edge of elem1 to the left edge of the page
        expected_bbox = BoundingBox(0, 100, 50, 51)
        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem1, expected_bbox),
                call(pdf_elem2, expected_bbox),
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 2)
        self.assertIn(pdf_elem2, result)
        self.assertIn(pdf_elem4, result)

        # Also test with inclusive=True
        partially_within_mock.reset_mock()
        result = elem_list.horizontally_in_line_with(pdf_elem1, inclusive=True)

        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem1, expected_bbox),
                call(pdf_elem2, expected_bbox),
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 3)
        self.assertIn(pdf_elem1, result)
        self.assertIn(pdf_elem2, result)
        self.assertIn(pdf_elem4, result)

    @patch.object(PDFElement, "partially_within", autospec=True)
    def test_filter_partially_within_bounding_box(self, partially_within_mock):
        partially_within_mock.side_effect = (
            lambda self, bounding_box: self.text == "within"
        )

        elem1 = FakePDFMinerTextElement(text="within")
        elem2 = FakePDFMinerTextElement(text="within")
        elem3 = FakePDFMinerTextElement()
        elem4 = FakePDFMinerTextElement(text="within")
        elem5 = FakePDFMinerTextElement()
        elem6 = FakePDFMinerTextElement(text="within")

        page1 = Page(elements=[elem1, elem2, elem3, elem4], width=100, height=100)
        page2 = Page(elements=[elem5, elem6], width=100, height=100)

        doc = PDFDocument(pages={1: page1, 2: page2})
        elem_list = doc.elements

        pdf_elem1 = self.__extract_element_from_list(elem1, elem_list)
        pdf_elem2 = self.__extract_element_from_list(elem2, elem_list)
        pdf_elem3 = self.__extract_element_from_list(elem3, elem_list)
        pdf_elem4 = self.__extract_element_from_list(elem4, elem_list)

        result = elem_list.filter_partially_within_bounding_box(
            BoundingBox(0, 1, 0, 1), 1
        )

        # expected_bbox is from the left edge of elem1 to the left edge of the page
        expected_bbox = BoundingBox(0, 1, 0, 1)
        partially_within_mock.assert_has_calls(
            [
                call(pdf_elem1, expected_bbox),
                call(pdf_elem2, expected_bbox),
                call(pdf_elem3, expected_bbox),
                call(pdf_elem4, expected_bbox),
            ],
            any_order=True,
        )

        self.assertEqual(len(result), 3)
        self.assertIn(pdf_elem1, result)
        self.assertIn(pdf_elem2, result)
        self.assertIn(pdf_elem4, result)

    def test_before(self):
        result = self.elem_list.before(self.elem_list[2])

        self.assertEqual(len(result), 2)
        self.assertIn(self.elem_list[0], result)
        self.assertIn(self.elem_list[1], result)

        result = self.elem_list.before(self.elem_list[2], inclusive=True)

        self.assertEqual(len(result), 3)
        self.assertIn(self.elem_list[0], result)
        self.assertIn(self.elem_list[1], result)
        self.assertIn(self.elem_list[2], result)

    def test_after(self):
        result = self.elem_list.after(self.elem_list[3])

        self.assertEqual(len(result), 2)
        self.assertIn(self.elem_list[4], result)
        self.assertIn(self.elem_list[5], result)

        result = self.elem_list.after(self.elem_list[3], inclusive=True)

        self.assertEqual(len(result), 3)
        self.assertIn(self.elem_list[3], result)
        self.assertIn(self.elem_list[4], result)
        self.assertIn(self.elem_list[5], result)

    def test_between(self):
        result = self.elem_list.between(self.elem_list[2], self.elem_list[5])

        self.assertEqual(len(result), 2)
        self.assertIn(self.elem_list[3], result)
        self.assertIn(self.elem_list[4], result)

        result = self.elem_list.between(
            self.elem_list[2], self.elem_list[5], inclusive=True
        )

        self.assertEqual(len(result), 4)
        self.assertIn(self.elem_list[2], result)
        self.assertIn(self.elem_list[3], result)
        self.assertIn(self.elem_list[4], result)
        self.assertIn(self.elem_list[5], result)

    def test_extract_single_element(self):
        with self.assertRaises(MultipleElementsFoundError):
            self.elem_list.extract_single_element()

        with self.assertRaises(NoElementFoundError):
            self.elem_list.filter_by_tag("non_existent_tag").extract_single_element()

        elem1 = FakePDFMinerTextElement()
        page = Page(elements=[elem1], width=100, height=100)
        doc = PDFDocument(pages={1: page})
        pdf_elem_1 = self.__extract_element_from_list(elem1, doc.elements)

        result = doc.elements.extract_single_element()
        self.assertEqual(result, pdf_elem_1)

    def test_add_element(self):
        empty_elem_list = self.elem_list.filter_by_tag("non_existent_tag")

        result = empty_elem_list.add_element(self.elem_list[0])
        self.assertEqual(len(result), 1)
        self.assertIn(self.elem_list[0], result)

        result = result.add_element(self.elem_list[0])
        self.assertEqual(len(result), 1)
        self.assertIn(self.elem_list[0], result)

        result = result.add_element(self.elem_list[4])
        self.assertEqual(len(result), 2)
        self.assertIn(self.elem_list[0], result)
        self.assertIn(self.elem_list[4], result)

    def test_add_elements(self):
        empty_elem_list = self.elem_list.filter_by_tag("non_existent_tag")

        result = empty_elem_list.add_elements(self.elem_list[0], self.elem_list[1])
        self.assertEqual(len(result), 2)
        self.assertIn(self.elem_list[0], result)
        self.assertIn(self.elem_list[1], result)

    def test_remove_element(self):
        original_length = len(self.elem_list)

        result = self.elem_list.remove_element(self.elem_list[0])
        self.assertEqual(len(result), original_length - 1)
        self.assertNotIn(self.elem_list[0], result)

        result = result.remove_element(self.elem_list[0])
        self.assertEqual(len(result), original_length - 1)
        self.assertNotIn(self.elem_list[0], result)

        result = result.remove_element(self.elem_list[4])
        self.assertEqual(len(result), original_length - 2)
        self.assertNotIn(self.elem_list[0], result)
        self.assertNotIn(self.elem_list[4], result)

    def test_remove_elements(self):
        original_length = len(self.elem_list)
        result = self.elem_list.remove_elements(self.elem_list[0], self.elem_list[1])
        self.assertEqual(len(result), original_length - 2)
        self.assertNotIn(self.elem_list[0], result)
        self.assertNotIn(self.elem_list[1], result)

    def test_repr(self):
        self.assertEqual(repr(self.elem_list), "<ElementList of 6 elements>")

    def test_getitem(self):
        self.__assert_original_element_equal(self.elem1, self.elem_list[0])

    def test_eq(self):
        with self.assertRaises(NotImplementedError):
            self.elem_list == "foo"

        second_elem_list = ElementList(self.doc, set([0, 1, 2, 3, 4, 5]))
        self.assertTrue(self.elem_list == second_elem_list)

        # Test with different indexes
        second_elem_list = ElementList(self.doc, set([0, 1, 2, 3, 4]))
        self.assertFalse(self.elem_list == second_elem_list)

        # Test with different document
        doc = PDFDocument(
            pages={
                1: Page(
                    elements=[
                        FakePDFMinerTextElement(),
                        FakePDFMinerTextElement(),
                        FakePDFMinerTextElement(),
                        FakePDFMinerTextElement(),
                        FakePDFMinerTextElement(),
                        FakePDFMinerTextElement(),
                    ],
                    width=100,
                    height=100,
                )
            }
        )
        second_elem_list = ElementList(doc, set([0, 1, 2, 3, 4, 5]))
        self.assertFalse(self.elem_list == second_elem_list)

    def test_len(self):
        self.assertEqual(len(self.elem_list), 6)

    def test_sub(self):
        list_1 = ElementList(self.doc, set([0, 1, 2, 3, 4, 5]))
        list_2 = ElementList(self.doc, set([0, 2]))

        result = list_1 - list_2
        self.assertEqual(result, ElementList(self.doc, set([1, 3, 4, 5])))

    def test_or(self):
        list_1 = ElementList(self.doc, set([0, 2]))
        list_2 = ElementList(self.doc, set([2, 3, 4]))

        result = list_1 | list_2
        self.assertEqual(result, ElementList(self.doc, set([0, 2, 3, 4])))

    def test_xor(self):
        list_1 = ElementList(self.doc, set([0, 2]))
        list_2 = ElementList(self.doc, set([2, 3, 4]))

        result = list_1 ^ list_2
        self.assertEqual(result, ElementList(self.doc, set([0, 3, 4])))

    def test_and(self):
        list_1 = ElementList(self.doc, set([0, 2]))
        list_2 = ElementList(self.doc, set([2, 3, 4]))

        result = list_1 & list_2
        self.assertEqual(result, ElementList(self.doc, set([2])))

    # Helper functions
    def __assert_original_element_in(self, original_element, element_list):
        pdf_element = self.__extract_element_from_list(original_element, element_list)
        self.assertIn(pdf_element, element_list)

    def __assert_original_element_equal(self, original_element, element):
        self.assertEqual(original_element, element.original_element)

    def __extract_element_from_list(self, original_element, element_list):
        return [
            elem for elem in element_list if elem.original_element == original_element
        ][0]
