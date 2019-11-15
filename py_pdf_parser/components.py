from typing import Dict, List, Optional

from collections import namedtuple

from pdfminer.layout import LTComponent

from .common import BoundingBox
from .filtering import ElementList
from .sectioning import Sectioning
from .utils import Utils

Page = namedtuple("Page", ["width", "height", "elements"])
PageInfo = namedtuple("PageInfo", ["width", "height", "start_element", "end_element"])


class PDFElement:
    original_element: LTComponent
    tags: List[str]
    ignore: bool
    bounding_box: BoundingBox
    __fontname: Optional[str] = None
    __fontsize: Optional[int] = None

    def __init__(self, element: LTComponent):
        self.original_element = element

        self.tags = []
        self.ignore = False

        self.bounding_box = BoundingBox(
            x0=element.x0, x1=element.x1, y0=element.y0, y1=element.y1
        )

    @property
    def fontname(self) -> str:
        if self.__fontname is not None:
            return self.__fontname

        first_line = next(iter(self.original_element))
        first_character = next(iter(first_line))

        self.__fontname = first_character.fontname
        return self.__fontname

    @property
    def fontsize(self) -> int:
        if self.__fontsize is not None:
            return self.__fontsize

        first_line = next(iter(self.original_element))
        first_character = next(iter(first_line))

        self.__fontsize = int(round(first_character.height, 0))
        return self.__fontsize

    @property
    def font(self) -> str:
        return f"{self.fontname},{self.fontsize}"

    @property
    def text(self) -> str:
        return self.original_element.get_text()

    def add_tag(self, new_tag: str):
        if new_tag not in self.tags:
            self.tags.append(new_tag)

    def entirely_within(self, bounding_box: BoundingBox) -> bool:
        """
        Returns whether each edge of the element is inside the bouding box.
        """
        return all(
            [
                self.bounding_box.x0 >= bounding_box.x0,
                self.bounding_box.x1 <= bounding_box.x1,
                self.bounding_box.y0 >= bounding_box.y0,
                self.bounding_box.y1 <= bounding_box.y1,
            ]
        )

    def partially_within(self, bounding_box: BoundingBox) -> bool:
        """
        TODO: This currently returns true of an entire edge of the element is within
        the box, which isn't quite what we want.
        """
        bottom_within = all(
            [
                bounding_box.x0 <= self.bounding_box.x0 <= bounding_box.x1,
                bounding_box.x0 <= self.bounding_box.x1 <= bounding_box.x1,
                bounding_box.y0 <= self.bounding_box.y0 <= bounding_box.y1,
            ]
        )
        top_within = all(
            [
                bounding_box.x0 <= self.bounding_box.x0 <= bounding_box.x1,
                bounding_box.x0 <= self.bounding_box.x1 <= bounding_box.x1,
                bounding_box.y0 <= self.bounding_box.y1 <= bounding_box.y1,
            ]
        )

        left_within = all(
            [
                bounding_box.y0 <= self.bounding_box.y0 <= bounding_box.y1,
                bounding_box.y0 <= self.bounding_box.y1 <= bounding_box.y1,
                bounding_box.x0 <= self.bounding_box.x0 <= bounding_box.x1,
            ]
        )
        right_within = all(
            [
                bounding_box.y0 <= self.bounding_box.y0 <= bounding_box.y1,
                bounding_box.y0 <= self.bounding_box.y1 <= bounding_box.y1,
                bounding_box.x0 <= self.bounding_box.x0 <= bounding_box.x1,
            ]
        )
        return any([bottom_within, top_within, left_within, right_within])


class PDFDocument:
    """
    PDFDocument ... #TODO

    elements: Ordered list of PDFElements.
    page_info: Mapping between page number and PageInfo namedtuples.
    """

    __element_map: Dict[int, int] = {}  # Mapping of elements to index in the list
    element_list: List[PDFElement] = []
    page_info: Dict[int, PageInfo] = {}
    number_of_pages: int
    pdf_file_path: Optional[str]

    def __init__(self, pages: Dict[int, Page], pdf_file_path: Optional[str] = None):
        self.sectioning = Sectioning(self)
        self.utils = Utils(self)
        idx = 0
        for page_number, page in pages.items():
            self.page_info[page_number] = PageInfo(
                width=page.width,
                height=page.height,
                start_element=page.elements[0],
                end_element=page.elements[-1],
            )

            for element in page.elements:
                self.element_list.append(element)
                self.__element_map[hash(element)] = idx
                idx += 1

        if len(self.element_list) != len(self.__element_map):
            raise Exception("Hash collision?")  # TODO

        self.pdf_file_path = pdf_file_path
        self.number_of_pages = len(pages)

    def element_index(self, element: PDFElement) -> int:
        return self.__element_map[hash(element)]

    def element_page(self, element: PDFElement) -> int:
        element_index = self.element_index(element)
        for page_number, page_info in self.page_info.items():
            if (
                self.element_index(page_info.start_element)
                <= element_index
                <= self.element_index(page_info.end_element)
            ):
                return page_number

    @property
    def elements(self) -> "ElementList":
        return ElementList(self)

    @property
    def pages(self) -> "PageIterator":
        return PageIterator(self)


class PageIterator:
    """
    TODO: This should return an object with page info and elements.
    """

    def __init__(self, document: "PDFDocument"):
        self.indexes = iter(range(1, document.number_of_pages + 1))
        self.document = document

    def __next__(self) -> "ElementList":
        index = next(self.indexes)
        return self.document.elements.filter_by_page(index)

    def __iter__(self):
        return self

    def __getitem__(self, index: int) -> "ElementList":
        # TODO: This should be get_page or something
        return self.document.elements.filter_by_page(index)
