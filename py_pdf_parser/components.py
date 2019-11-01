from typing import Dict, List, Optional, Iterator

from collections import namedtuple

from pdfminer.layout import LTComponent


PageInfo = namedtuple("PageInfo", ["width", "height", "start_index", "end_index"])
BoundingBox = namedtuple("BoundingBox", ["x0", "x1", "y0", "y1", "width", "height"])


class PDFElement:
    original_element: LTComponent
    page_number: int
    tags: List[str]
    ignore: bool
    bounding_box: BoundingBox
    __fontname: Optional[str] = None
    __fontsize: Optional[int] = None

    def __init__(self, element: LTComponent, page_number: int):
        self.original_element = element
        self.page_number = page_number

        self.tags = []
        self.ignore = False

        self.bounding_box = BoundingBox(
            x0=element.x0,
            x1=element.x1,
            y0=element.y0,
            y1=element.y1,
            width=element.x1 - element.x0,
            height=element.y1 - element.y0,
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

    def add_tag(self, new_tag: str):
        if new_tag not in self.tags:
            self.tags.append(new_tag)


class PDFDocument:
    """
    PDFDocument ... #TODO

    elements: Ordered list of PDFElements.
    page_info: Mapping between page number and PageInfo namedtuples.
    """

    elements: List[PDFElement]
    page_info: Dict[int, PageInfo]
    number_of_pages: int
    pdf_file_path: Optional[str]

    def __init__(
        self,
        elements: List[PDFElement],
        page_info: Dict[int, PageInfo],
        pdf_file_path: Optional[str] = None,
    ):
        self.elements = elements
        self.page_info = page_info
        self.pdf_file_path = pdf_file_path
        self.number_of_pages = len(page_info)

    def elements_for_page(
        self, page_number: int, include_ignored: bool = False
    ) -> Iterator[PDFElement]:
        page_info = self.page_info[page_number]
        return filter(
            lambda elem: include_ignored or not elem.ignore,
            self.elements[page_info.start_index : page_info.end_index],
        )
