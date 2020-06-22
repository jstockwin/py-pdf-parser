import re

from ddt import ddt, data

from py_pdf_parser.common import BoundingBox
from py_pdf_parser.components import PDFDocument, ElementOrdering
from py_pdf_parser.filtering import ElementList
from py_pdf_parser.loaders import Page
from py_pdf_parser.exceptions import NoElementsOnPageError, PageNotFoundError

from .base import BaseTestCase
from .utils import create_pdf_element, create_pdf_document, FakePDFMinerTextElement


@ddt
class TestPDFElement(BaseTestCase):
    element_bbox = BoundingBox(2, 5, 2, 5)

    def test_page_number(self):
        element = create_pdf_element()
        self.assertEqual(element.page_number, 1)

        with self.assertRaises(AttributeError):
            element.page_number = 2

    def test_font_name(self):
        element = create_pdf_element(font_name="test_font")
        self.assertEqual(element.font_name, "test_font")

    def test_font_size(self):
        element = create_pdf_element(font_size=2)
        self.assertEqual(element.font_size, 2)

    def test_font_size_precision(self):
        element = create_pdf_element(font_size=1.234)
        self.assertEqual(element.font_size, 1.2)

        element = create_pdf_element(font_size=1.234, font_size_precision=0)
        self.assertEqual(element.font_size, 1)

        element = create_pdf_element(font_size=1.234, font_size_precision=3)
        self.assertEqual(element.font_size, 1.234)

    def test_font(self):
        element = create_pdf_element(font_name="test_font", font_size=2)
        self.assertEqual(element.font, "test_font,2")

        element = create_pdf_element(
            font_name="test_font",
            font_size=3,
            font_mapping={"test_font,3": "test_named_font"},
        )
        self.assertEqual(element.font, "test_named_font")

        element = create_pdf_element(
            font_name="test_font",
            font_size=2,
            font_mapping={"test_font,3": "test_named_font"},
        )
        self.assertEqual(element.font, "test_font,2")

        # Test when font_mapping argument is passed to PDFDocument
        font_mapping = {}
        element = create_pdf_element(
            font_name="fake_font_1", font_size=10, font_mapping=font_mapping
        )
        self.assertEqual(element.font, "fake_font_1,10")

        font_mapping = {"fake_font_1,10": "large_text"}
        element = create_pdf_element(
            font_name="fake_font_1", font_size=10, font_mapping=font_mapping
        )
        self.assertEqual(element.font, "large_text")

        font_mapping = {r"^fake_font_\d,10$": "large_text"}
        element = create_pdf_element(
            font_name="fake_font_1",
            font_size=10,
            font_mapping=font_mapping,
            font_mapping_is_regex=True,
        )
        self.assertEqual(element.font, "large_text")

        font_mapping = {r"^fake_font_\d,10$": "large_text"}
        element = create_pdf_element(
            font_name="FAKE_FONT_1",
            font_size=10,
            font_mapping=font_mapping,
            font_mapping_is_regex=True,
        )
        self.assertEqual(element.font, "FAKE_FONT_1,10")

        font_mapping = {r"^fake_font_\d,10$": "large_text"}
        element = create_pdf_element(
            font_name="FAKE_FONT_1",
            font_size=10,
            font_mapping=font_mapping,
            font_mapping_is_regex=True,
            regex_flags=re.IGNORECASE,
        )
        self.assertEqual(element.font, "large_text")

    def test_text(self):
        element = create_pdf_element(text=" test ")
        self.assertEqual(element.text(), "test")
        self.assertEqual(element.text(stripped=False), " test ")

    def test_add_tag(self):
        element = create_pdf_element()
        self.assertEqual(element.tags, set())

        element.add_tag("foo")
        self.assertEqual(element.tags, set(["foo"]))

        element.add_tag("foo")
        self.assertEqual(element.tags, set(["foo"]))

        element.add_tag("bar")
        self.assertEqual(element.tags, set(["foo", "bar"]))

    def test_repr(self):
        element = create_pdf_element(font_name="test_font", font_size=2)
        self.assertEqual(repr(element), "<PDFElement tags: set(), font: 'test_font,2'>")

        element.add_tag("foo")
        self.assertEqual(
            repr(element), "<PDFElement tags: {'foo'}, font: 'test_font,2'>"
        )

        element.ignore()
        self.assertEqual(
            repr(element), "<PDFElement tags: {'foo'}, font: 'test_font,2', ignored>"
        )

    @data(
        BoundingBox(1, 6, 1, 6),  # This box fully encloses the element
        BoundingBox(1, 6, 0, 3),  # This box intersects the bottom of the element
        BoundingBox(1, 6, 0, 2),  # This box touches the bottom of the element
        BoundingBox(1, 6, 4, 6),  # This box intersects the top of the element
        BoundingBox(1, 6, 5, 6),  # This box touches the top of the element
        BoundingBox(1, 6, 3, 4),  # This box goes through center horizontally
        BoundingBox(1, 3, 1, 6),  # This box intersects the left of the element
        BoundingBox(1, 2, 1, 6),  # This box touches the left of the element
        BoundingBox(4, 6, 1, 6),  # This box intersects the left of the element
        BoundingBox(5, 6, 1, 6),  # This box touches the left of the element
        BoundingBox(3, 4, 1, 6),  # This box goes through the center vertically
        BoundingBox(3, 4, 3, 4),  # This box is enclosed inside the element
    )
    def test_partially_within_true(self, bounding_box):
        element = create_pdf_element(self.element_bbox)
        self.assertTrue(element.partially_within(bounding_box))

    @data(
        BoundingBox(1, 6, 0, 1),  # This box is underneath the element
        BoundingBox(1, 6, 6, 7),  # This box is above the element
        BoundingBox(0, 1, 1, 6),  # This box is to the left of the element
        BoundingBox(6, 7, 1, 6),  # This box is to the lerightft of the element
    )
    def test_partially_within_false(self, bounding_box):
        element = create_pdf_element(self.element_bbox)
        self.assertFalse(element.partially_within(bounding_box))

    @data(BoundingBox(1, 6, 1, 6))  # This box fully encloses the element
    def test_entirely_within_true(self, bounding_box):
        element = create_pdf_element(self.element_bbox)
        self.assertTrue(element.entirely_within(bounding_box))

    @data(
        BoundingBox(1, 6, 0, 3),  # This box intersects the bottom of the element
        BoundingBox(1, 6, 0, 2),  # This box touches the bottom of the element
        BoundingBox(1, 6, 4, 6),  # This box intersects the top of the element
        BoundingBox(1, 6, 5, 6),  # This box touches the top of the element
        BoundingBox(1, 6, 3, 4),  # This box goes through center horizontally
        BoundingBox(1, 3, 1, 6),  # This box intersects the left of the element
        BoundingBox(1, 2, 1, 6),  # This box touches the left of the element
        BoundingBox(4, 6, 1, 6),  # This box intersects the left of the element
        BoundingBox(5, 6, 1, 6),  # This box touches the left of the element
        BoundingBox(3, 4, 1, 6),  # This box goes through the center vertically
        BoundingBox(1, 6, 0, 1),  # This box is underneath the element
        BoundingBox(1, 6, 6, 7),  # This box is above the element
        BoundingBox(0, 1, 1, 6),  # This box is to the left of the element
        BoundingBox(6, 7, 1, 6),  # This box is to the right of the element
        BoundingBox(3, 4, 3, 4),  # This box is enclosed inside the element
    )
    def test_entirely_within_false(self, bounding_box):
        element = create_pdf_element(self.element_bbox)
        self.assertFalse(element.entirely_within(bounding_box))


class TestPDFDocument(BaseTestCase):
    def test_document(self):
        el_page_1_top_left = FakePDFMinerTextElement(BoundingBox(0, 1, 2, 3))
        el_page_1_top_right = FakePDFMinerTextElement(BoundingBox(2, 3, 2, 3))
        el_page_1_bottom_left = FakePDFMinerTextElement(BoundingBox(0, 1, 0, 1))
        el_page_1_bottom_right = FakePDFMinerTextElement(BoundingBox(2, 3, 0, 1))
        page_1 = Page(
            elements=[
                el_page_1_top_left,
                el_page_1_top_right,
                el_page_1_bottom_left,
                el_page_1_bottom_right,
            ],
            width=100,
            height=100,
        )

        el_page_2_top_left = FakePDFMinerTextElement(BoundingBox(0, 1, 2, 3))
        el_page_2_top_right = FakePDFMinerTextElement(BoundingBox(2, 3, 2, 3))
        el_page_2_bottom_left = FakePDFMinerTextElement(BoundingBox(0, 1, 0, 1))
        el_page_2_bottom_right = FakePDFMinerTextElement(BoundingBox(2, 3, 0, 1))
        page_2 = Page(
            elements=[
                el_page_2_bottom_right,
                el_page_2_bottom_left,
                el_page_2_top_right,
                el_page_2_top_left,
            ],
            width=100,
            height=100,
        )

        document = PDFDocument(pages={1: page_1, 2: page_2})

        # Checks elements were reordered
        expected_ordered_list = [
            el_page_1_top_left,
            el_page_1_top_right,
            el_page_1_bottom_left,
            el_page_1_bottom_right,
            el_page_2_top_left,
            el_page_2_top_right,
            el_page_2_bottom_left,
            el_page_2_bottom_right,
        ]
        self.assertEqual(
            [elem.original_element for elem in document._element_list],
            expected_ordered_list,
        )

        # Checks indexes were assigned properly
        self.assertEqual(
            [elem._index for elem in document._element_list], [0, 1, 2, 3, 4, 5, 6, 7]
        )

        # Checks page numbers is correct
        self.assertEqual(document.page_numbers, [1, 2])

        # Checks number of pages is correct
        self.assertEqual(document.number_of_pages, 2)

        # Checks pages were assigned properly
        self.assertEqual(
            [elem.page_number for elem in document._element_list],
            [1, 1, 1, 1, 2, 2, 2, 2],
        )

        # Checks pages were instantiated correctly
        pdf_page_1 = document.get_page(1)
        self.assertEqual(page_1.width, pdf_page_1.width)
        self.assertEqual(page_1.height, pdf_page_1.height)
        self.assertEqual(el_page_1_top_left, pdf_page_1.start_element.original_element)
        self.assertEqual(
            el_page_1_bottom_right, pdf_page_1.end_element.original_element
        )
        self.assertEqual(pdf_page_1.page_number, 1)
        self.assertEqual(pdf_page_1.elements, ElementList(document, set([0, 1, 2, 3])))

        pdf_page_2 = document.get_page(2)
        self.assertEqual(page_2.width, pdf_page_2.width)
        self.assertEqual(page_2.height, pdf_page_2.height)
        self.assertEqual(el_page_2_top_left, pdf_page_2.start_element.original_element)
        self.assertEqual(
            el_page_2_bottom_right, pdf_page_2.end_element.original_element
        )
        self.assertEqual(pdf_page_2.page_number, 2)
        self.assertEqual(pdf_page_2.elements, ElementList(document, set([4, 5, 6, 7])))

        self.assertEqual(document.pages, [pdf_page_1, pdf_page_2])

        self.assertEqual(
            document.elements, ElementList(document, set([0, 1, 2, 3, 4, 5, 6, 7]))
        )
        with self.assertRaises(PageNotFoundError):
            document.get_page(3)

    def test_document_with_blank_page(self):
        with self.assertRaises(NoElementsOnPageError):
            PDFDocument(pages={1: Page(elements=[], width=100, height=100)})

    def test_element_ordering(self):
        #       elem_1      elem_2
        #       elem_3      elem_4
        elem_1 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 6, 10))
        elem_2 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 6, 10))
        elem_3 = FakePDFMinerTextElement(bounding_box=BoundingBox(0, 5, 0, 5))
        elem_4 = FakePDFMinerTextElement(bounding_box=BoundingBox(6, 10, 0, 5))

        # Check default: left to right, top to bottom
        document = create_pdf_document(elements=[elem_1, elem_2, elem_3, elem_4])
        self.assert_original_element_list_equal(
            [elem_1, elem_2, elem_3, elem_4], document.elements
        )

        # Check other presets
        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4],
            element_ordering=ElementOrdering.RIGHT_TO_LEFT_TOP_TO_BOTTOM,
        )
        self.assert_original_element_list_equal(
            [elem_2, elem_1, elem_4, elem_3], document.elements
        )

        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4],
            element_ordering=ElementOrdering.TOP_TO_BOTTOM_LEFT_TO_RIGHT,
        )
        self.assert_original_element_list_equal(
            [elem_1, elem_3, elem_2, elem_4], document.elements
        )

        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4],
            element_ordering=ElementOrdering.TOP_TO_BOTTOM_RIGHT_TO_LEFT,
        )
        self.assert_original_element_list_equal(
            [elem_2, elem_4, elem_1, elem_3], document.elements
        )

        # Check custom function
        document = create_pdf_document(
            elements=[elem_1, elem_2, elem_3, elem_4],
            element_ordering=lambda elements: [
                elements[0],
                elements[3],
                elements[1],
                elements[2],
            ],
        )
        self.assert_original_element_list_equal(
            [elem_1, elem_4, elem_2, elem_3], document.elements
        )
