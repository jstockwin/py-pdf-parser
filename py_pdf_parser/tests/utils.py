from typing import NamedTuple, Dict, Optional

from py_pdf_parser.components import PDFElement
from pdfminer.layout import LTComponent

from py_pdf_parser.common import BoundingBox


class FakePDFMinerCharacter(NamedTuple):
    fontname: str = "fake_fontname"
    height: int = 10


class FakePDFMinerIterator:
    def __init__(self, font_name: str = "fake_font", font_size: int = 10):
        self.finished = False
        self.font_name = font_name
        self.font_size = font_size

    def __next__(self):
        if self.finished:
            raise StopIteration()

        self.finished = True
        return [FakePDFMinerCharacter(fontname=self.font_name, height=self.font_size)]


class FakePDFMinerTextElement(LTComponent):
    """
    This is a stub to help create something which looks like a PDFMiner text element
    for use in testing.

    The fontname and size are detected by getting the first character of the first row
    of the contained text. This is done by iterating, hence we define an iterator which
    simply returns one list of length one and then raises StopIteration. This is the
    minimum needed to pretend to allow extraction of the first character, for which
    we use the FakeCharacter namedtuple which has fontname and height attibutes set.
    """

    def __init__(
        self,
        bounding_box: "BoundingBox" = BoundingBox(0, 1, 0, 1),
        text: str = "fake_text",
        font_name: str = "fake_font",
        font_size: int = 10,
    ):
        super().__init__(
            bbox=[bounding_box.x0, bounding_box.y0, bounding_box.x1, bounding_box.y1]
        )
        self.text = text
        self.font_name = font_name
        self.font_size = font_size

    def __iter__(self):
        return FakePDFMinerIterator(font_name=self.font_name, font_size=self.font_size)

    def get_text(self) -> str:
        if self.text is None:
            return ""
        return self.text


def create_pdf_element(
    bounding_box: "BoundingBox" = BoundingBox(0, 1, 0, 1),
    index: int = 0,
    page_number: int = 1,
    text: str = "fake_text",
    font_name: str = "fake_font",
    font_size: int = 10,
    font_mapping: Optional[Dict[str, str]] = None,
):
    return PDFElement(
        element=FakePDFMinerTextElement(
            bounding_box, text=text, font_name=font_name, font_size=font_size
        ),
        index=index,
        page_number=page_number,
        font_mapping=font_mapping,
    )
