import re

from typing import NamedTuple, Callable, Dict, List, Optional, Union

from py_pdf_parser.components import PDFElement, PDFDocument, ElementOrdering
from py_pdf_parser.sectioning import Section
from pdfminer.layout import LTComponent

from py_pdf_parser.common import BoundingBox
from py_pdf_parser.loaders import Page


class FakePDFMinerCharacter(NamedTuple):
    fontname: str = "fake_fontname"
    height: float = 10


class FakePDFMinerIterator:
    def __init__(self, font_name: str = "fake_font", font_size: float = 10):
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
        font_size: float = 10,
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
    text: str = "fake_text",
    font_name: str = "fake_font",
    font_size: float = 10,
    font_mapping: Optional[Dict[str, str]] = None,
    font_mapping_is_regex: bool = False,
    regex_flags: Union[int, re.RegexFlag] = 0,
    font_size_precision: int = 1,
) -> "PDFElement":
    document = create_pdf_document(
        elements=[
            FakePDFMinerTextElement(
                bounding_box, text=text, font_name=font_name, font_size=font_size
            )
        ],
        font_mapping=font_mapping,
        font_mapping_is_regex=font_mapping_is_regex,
        regex_flags=regex_flags,
        font_size_precision=font_size_precision,
    )
    return document.elements[0]


def create_pdf_document(
    elements: Union[List[LTComponent], Dict[int, List[LTComponent]]],
    font_mapping: Optional[Dict[str, str]] = None,
    font_mapping_is_regex: bool = False,
    regex_flags: Union[int, re.RegexFlag] = 0,
    font_size_precision: int = 1,
    element_ordering: Union[
        ElementOrdering, Callable[[List], List]
    ] = ElementOrdering.LEFT_TO_RIGHT_TOP_TO_BOTTOM,
) -> "PDFDocument":
    """
    Creates a PDF document with the given elements.
    "elements" can be a list of elements (in which case a document with a single page
    will be created) or a dictionary mapping page number to its list of elements.
    """
    if not isinstance(elements, dict):
        pages = {1: Page(elements=elements, width=100, height=100)}
    else:
        pages = {
            page_number: Page(elements=elements_list, width=100, height=100)
            for page_number, elements_list in elements.items()
        }

    return PDFDocument(
        pages=pages,
        font_mapping=font_mapping,
        font_mapping_is_regex=font_mapping_is_regex,
        regex_flags=regex_flags,
        font_size_precision=font_size_precision,
        element_ordering=element_ordering,
    )


def create_section(
    document: "PDFDocument",
    name: str = "fake_name",
    unique_name: str = "fake_name_1",
    start_element: Optional["PDFElement"] = None,
    end_element: Optional["PDFElement"] = None,
) -> "Section":
    """
    Creates a simple section
    """
    if start_element is None:
        start_element = document._element_list[0]
    if end_element is None:
        end_element = document._element_list[-1]

    return Section(document, name, unique_name, start_element, end_element)
