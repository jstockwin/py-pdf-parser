from typing import Dict, List, IO, Any, Optional, Iterator

from collections import namedtuple

from pdfminer import converter, layout, pdfdocument, pdfinterp, pdfpage, pdfparser
from pdfminer.layout import LTComponent, LTTextContainer, LAParams


PageInfo = namedtuple("PageInfo", ["width", "height", "start_index", "end_index"])
BoundingBox = namedtuple("BoundingBox", ["x0", "x1", "y0", "y1", "width", "height"])


class PDFElement:
    original_element: LTComponent
    page_number: int
    tags: List[str]
    ignore: bool
    bounding_box: BoundingBox

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


def load_file(path_to_file: str) -> PDFDocument:
    with open(path_to_file, "rb") as in_file:
        return load(in_file, pdf_file_path=path_to_file)


def load(pdf_file: IO, pdf_file_path: Optional[str] = None) -> PDFDocument:
    parser = pdfparser.PDFParser(pdf_file)
    document = pdfdocument.PDFDocument(parser)

    if not document.is_extractable:
        raise pdfpage.PDFTextExtractionNotAllowed

    resource_manager = pdfinterp.PDFResourceManager()
    device = converter.PDFPageAggregator(
        resource_manager, laparams=LAParams()
    )  # TODO laparams
    interpreter = pdfinterp.PDFPageInterpreter(resource_manager, device)

    elements: List[PDFElement] = []
    page_info: Dict[int, PageInfo] = {}
    for page in pdfpage.PDFPage.create_pages(document):
        interpreter.process_page(page)
        results = device.get_result()

        page_number = results.pageid

        new_elements = [
            PDFElement(element=element, page_number=results.pageid)
            for element in results
            if isinstance(element, LTTextContainer)
        ]

        page_info[page_number] = PageInfo(
            width=results.width,
            height=results.height,
            start_index=len(elements),
            end_index=len(elements) + len(new_elements) - 1,
        )

        elements += new_elements

    return PDFDocument(
        elements=elements, page_info=page_info, pdf_file_path=pdf_file_path
    )
