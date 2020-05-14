from py_pdf_parser.common import BoundingBox
from py_pdf_parser.exceptions import InvalidCoordinatesError

from .base import BaseTestCase


class TestBoundingBox(BaseTestCase):
    def test_create_bounding_box(self):
        bbox = BoundingBox(0, 1, 0, 1)
        self.assertEqual(bbox.width, 1)
        self.assertEqual(bbox.height, 1)

        # Checks that it raises an exception if coordinates are not valid
        with self.assertRaises(InvalidCoordinatesError):
            BoundingBox(1, 0, 0, 1)

        with self.assertRaises(InvalidCoordinatesError):
            BoundingBox(0, 1, 1, 0)

    def test_eq(self):
        bbox_1 = BoundingBox(0, 1, 0, 1)
        bbox_2 = BoundingBox(0, 1, 0, 1)
        self.assertEqual(bbox_1, bbox_2)

        bbox_3 = BoundingBox(0, 1, 0, 3)
        self.assertNotEqual(bbox_1, bbox_3)

    def test_repr(self):
        bbox = BoundingBox(0, 1, 0, 1)
        self.assertEqual(repr(bbox), "<BoundingBox x0=0, x1=1, y0=0, y1=1>")
