from ddt import ddt, data
from unittest import TestCase

from py_pdf_parser.common import BoundingBox

from utils import create_element


@ddt
class TestElement(TestCase):
    element_bbox = BoundingBox(2, 5, 2, 5)

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
    )
    def test_partially_within_true(self, bounding_box):
        element = create_element(self.element_bbox)
        self.assertTrue(element.partially_within(bounding_box))

    @data(
        BoundingBox(1, 6, 0, 1),  # This box is underneath the element
        BoundingBox(1, 6, 6, 7),  # This box is above the element
        BoundingBox(0, 1, 1, 6),  # This box is to the left of the element
        BoundingBox(6, 7, 1, 6),  # This box is to the lerightft of the element
    )
    def test_partially_within_false(self, bounding_box):
        element = create_element(self.element_bbox)
        self.assertFalse(element.partially_within(bounding_box))

    @data(BoundingBox(1, 6, 1, 6))  # This box fully encloses the element
    def test_entirely_within_true(self, bounding_box):
        element = create_element(self.element_bbox)
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
        BoundingBox(6, 7, 1, 6),  # This box is to the lerightft of the element
    )
    def test_entirely_within_false(self, bounding_box):
        element = create_element(self.element_bbox)
        self.assertFalse(element.entirely_within(bounding_box))
