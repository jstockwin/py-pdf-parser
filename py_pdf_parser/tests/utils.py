from typing import TYPE_CHECKING

from py_pdf_parser.components import PDFElement
from pdfminer.layout import LTComponent

if TYPE_CHECKING:
    from py_pdf_parser.common import BoundingBox


def create_element(bounding_box: "BoundingBox", index: int = 0, page_number: int = 1):
    return PDFElement(
        element=LTComponent(
            bbox=[bounding_box.x0, bounding_box.y0, bounding_box.x1, bounding_box.y1]
        ),
        index=index,
        page_number=page_number,
    )
