from typing import Dict, List, Set, Optional, NamedTuple

from pdfminer.layout import LTComponent

from .common import BoundingBox
from .exceptions import PageNotFoundError, NoElementsOnPageError
from .filtering import ElementList
from .sectioning import Sectioning


class Page(NamedTuple):
    """
    This is used pass pages/elements when instantiating `PDFDocument`.

    Args:
        width (int): The width of the page.
        height (int): The height of the page.
        elements (int): A list of PDF Miner elements (`LTComponent`s) on the page.
    """

    width: int
    height: int
    elements: List[LTComponent]


class PDFPage:
    """
    A representation of a page within the `PDFDocument`.

    We store the width, height and page number of the page, along with the first and
    last element on the page. Because the elements are ordered, this allows us to easily
    determine all the elements on the page.

    Args:
        document (PDFDocument): A reference to the `PDFDocument`.
        width (int): The width of the page.
        height (int): The height of the page.
        page_number (int): Then page number of the page.
        start_element (PDFElement): The first element on the page.
        end_element (PDFElement): The last element on the page.
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
        """
        Returns an `ElementList` containing all elements on the page.
        """
        return self.document.elements.between(
            self.start_element, self.end_element, inclusive=True
        )


class PDFElement:
    """
    A representation of a single element within the pdf.

    You should not instantiate this yourself, but should let the `PDFDocument` do this.

    Args:
        element (LTComponent): A PDF Miner LTComponent.
        index (int): The index of the element within the document.
        page_number (int): The page number that the element is on.
        font_mapping (dict): See the `PDFDocument` documentation.

    Attributes:
        original_element (LTComponent): A reference to the original PDF Miner element.
        tags (set): A list of tags (str) that have been added to the element.
        ignore (bool): A flag specifying whether the element has been ignored.
        bounding_box (BoundingBox): The box representing the location of the element.
    """

    original_element: LTComponent
    tags: Set[str]
    ignore: bool
    bounding_box: BoundingBox
    __fontname: Optional[str] = None
    __fontsize: Optional[int] = None
    __font_mapping: Dict[str, str] = {}
    __index: Optional[int] = None
    __page_number: Optional[int] = None

    def __init__(
        self,
        element: LTComponent,
        index: int,
        page_number: int,
        font_mapping: Optional[Dict[str, str]] = None,
    ):
        self.original_element = element
        self.__index = index
        self.__page_number = page_number

        self.tags = set()
        self.ignore = False

        self.bounding_box = BoundingBox(
            x0=element.x0, x1=element.x1, y0=element.y0, y1=element.y1
        )
        if font_mapping is not None:
            self.__font_mapping = font_mapping

    @property
    def index(self):
        """
        The index of the element in the document, for internal use only.
        """
        return self.__index

    @property
    def page_number(self):
        """
        The page_number of the element in the document.
        """
        return self.__page_number

    @property
    def fontname(self) -> str:
        """
        The name of the font.

        This will be taken from the pdf itself, using the first character in the
        element.
        """
        if self.__fontname is not None:
            return self.__fontname

        first_line = next(iter(self.original_element))
        first_character = next(iter(first_line))

        self.__fontname = first_character.fontname
        return self.__fontname

    @property
    def fontsize(self) -> int:
        """
        The size of the font.

        This will be taken from the pdf itself, using the first character in the
        element.
        """
        if self.__fontsize is not None:
            return self.__fontsize

        first_line = next(iter(self.original_element))
        first_character = next(iter(first_line))

        self.__fontsize = int(round(first_character.height, 0))
        return self.__fontsize

    @property
    def font(self) -> str:
        """
        The name and size of the font, separated by a comma with no spaces.

        This will be taken from the pdf itself, using the first character in the
        element.

        If you have provided a font_mapping, this is the string you should map. If
        the string is mapped in your font_mapping then the mapped value will be
        returned.
        """
        font = f"{self.fontname},{self.fontsize}"
        return self.__font_mapping.get(font, font)

    @property
    def text(self) -> str:
        """
        The text contained in the element.
        """
        return self.original_element.get_text()

    def add_tag(self, new_tag: str):
        """
        Adds the `new_tag` to the tags set.
        """
        self.tags.add(new_tag)

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
        Whether any part of the element intersects with the given bounding box.
        """
        return all(
            [
                bounding_box.x0 <= self.bounding_box.x1,
                bounding_box.x1 >= self.bounding_box.x0,
                bounding_box.y0 <= self.bounding_box.y1,
                bounding_box.y1 >= self.bounding_box.y0,
            ]
        )

    def __repr__(self):
        return (
            f"<PDFElement tags: {self.tags}, font: '{self.font}''"
            f"{', ignored' if self.ignore else ''}>"
        )


class PDFDocument:
    """
    Contains all information about the whole pdf document.

    To instantiate, you should pass a dictionary mapping page numbers to pages, where
    each page is a Page namedtuple containing the width and heigh of the page, and a
    list of pdf elements (which should be directly from PDFMiner, i.e. should be
    PDFMiner `LTComponent`s). On instantiation, the PDFDocument will convert all of
    these into `PDFElement` classes.

    Args:
        pages (dict): A dictionary mapping page numbers (int) to pages, where pages are
            a `Page` namedtuple (containing a width, height and a list of elements from
            PDFMiner).
        pdf_file_path (str, optional): A file path to the PDF file. This is optional,
            and is only used to display your pdf as a background image when using the
            visualise functions.
        font_mapping (dict, optional): `PDFElement`s have a `font` attribute, and the
            font is taken from the PDF. You can map these fonts to instead use your own
            internal font names by providing a font_mapping. This is a dictionary with
            keys being the original font (including font size) and values being your
            new names.

    Attributes:
        element_list (list): A list of all the `PDFElements` in the document.
        pages (list): A list of all `PDFPages` in the document.
        number_of_pages (int): The total number of pages in the document.
        page_file_path (str, optional): The pdf file path, if provided.
        sectioning: Gives access to the sectioning utilities. See the documentation for
            the `Sectioning` class.
    """

    element_list: List[PDFElement] = []
    pages: List[PDFPage] = []
    number_of_pages: int
    pdf_file_path: Optional[str]

    def __init__(
        self,
        pages: Dict[int, Page],
        pdf_file_path: Optional[str] = None,
        font_mapping: Optional[Dict[str, str]] = None,
    ):
        self.sectioning = Sectioning(self)
        idx = 0
        for page_number, page in sorted(pages.items()):
            first_element = None
            for element in sorted(page.elements, key=lambda elem: (-elem.y0, elem.x0)):
                pdf_element = PDFElement(
                    element,
                    index=idx,
                    page_number=page_number,
                    font_mapping=font_mapping,
                )
                self.element_list.append(pdf_element)
                idx += 1
                if first_element is None:
                    first_element = pdf_element

            if first_element is None:
                raise NoElementsOnPageError(
                    f"No elements on page {page_number}, please exclude this page"
                )

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
        """
        Returns an `ElementList` containing all elements in the document.
        """
        return ElementList(self)

    def get_page(self, page_number: int) -> "PDFPage":
        """
        Returns the `PDFPage` for the specified `page_number`.

        Raises:
            PageNotFoundError: If `page_number` was not found.
        """
        for page in self.pages:
            if page.page_number == page_number:
                return page
        raise PageNotFoundError(f"Could not find page {page_number}")
