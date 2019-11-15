from typing import Dict, List, Optional, NamedTuple

from pdfminer.layout import LTComponent

from .common import BoundingBox
from .filtering import ElementList
from .sectioning import Sectioning
from .utils import Utils


class Page(NamedTuple):
    """
    This is used to load pages/elements into the PDF document.
    """

    width: int
    height: int
    elements: List[LTComponent]


class PDFPage:
    """
    This is what we use internally.
    """

    document: "PDFDocument"
    width: int
    height: int
    page_number: int
    start_element: "PDFElement"
    end_element: "PDFElement"

    def __init__(
        self,
        document: "PDFDocument",
        width: int,
        height: int,
        page_number: int,
        start_element: "PDFElement",
        end_element: "PDFElement",
    ):
        self.document = document
        self.width = width
        self.height = height
        self.page_number = page_number
        self.start_element = start_element
        self.end_element = end_element

    @property
    def elements(self) -> "ElementList":
        return self.document.elements.between(
            self.start_element, self.end_element, inclusive=True
        )


class PDFElement:
    original_element: LTComponent
    tags: List[str]
    ignore: bool
    bounding_box: BoundingBox
    __fontname: Optional[str] = None
    __fontsize: Optional[int] = None
    __index: Optional[int] = None
    __page_number: Optional[int] = None

    def __init__(self, element: LTComponent, index, page_number):
        self.original_element = element
        self.__index = index
        self.__page_number = page_number

        self.tags = []
        self.ignore = False

        self.bounding_box = BoundingBox(
            x0=element.x0, x1=element.x1, y0=element.y0, y1=element.y1
        )

    @property
    def index(self):
        if self.__index is None:
            return Exception("Index has not been set yet")
        return self.__index

    @index.setter
    def index(self, index):
        raise Exception("Index cannot be changed")

    @property
    def page_number(self):
        if self.__page_number is None:
            return Exception("page_number has not been set yet")
        return self.__page_number

    @page_number.setter
    def page_number(self, page_number):
        raise Exception("page_number cannot be changed")

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
    """

    element_list: List[PDFElement] = []
    pages: List[PDFPage] = []
    number_of_pages: int
    pdf_file_path: Optional[str]

    def __init__(self, pages: Dict[int, Page], pdf_file_path: Optional[str] = None):
        self.sectioning = Sectioning(self)
        self.utils = Utils(self)
        idx = 0
        for page_number, page in sorted(pages.items()):
            first_element = None
            for element in page.elements:
                pdf_element = PDFElement(element, index=idx, page_number=page_number)
                self.element_list.append(pdf_element)
                idx += 1
                if not first_element:
                    first_element = pdf_element

            if first_element is None:
                raise Exception("No elements on page")

            self.pages.append(
                PDFPage(
                    document=self,
                    width=page.width,
                    height=page.height,
                    page_number=page_number,
                    start_element=first_element,
                    end_element=pdf_element,
                )
            )

        self.pdf_file_path = pdf_file_path
        self.number_of_pages = len(pages)

    @property
    def elements(self) -> "ElementList":
        return ElementList(self)

    def get_page(self, page_number: int) -> "PDFPage":
        for page in self.pages:
            if page.page_number == page_number:
                return page
        raise Exception(f"Could not find page {page_number}")
