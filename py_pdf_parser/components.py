from typing import Callable, Dict, List, Set, Optional, Union, TYPE_CHECKING

import re
from collections import Counter, defaultdict
from enum import Enum, auto
from itertools import chain

from .common import BoundingBox
from .exceptions import PageNotFoundError, NoElementsOnPageError
from .filtering import ElementList
from .sectioning import Sectioning

if TYPE_CHECKING:
    from .loaders import Page
    from pdfminer.layout import LTComponent


class ElementOrdering(Enum):
    """
    A class enumerating the available presets for element_ordering.
    """

    LEFT_TO_RIGHT_TOP_TO_BOTTOM = auto()
    RIGHT_TO_LEFT_TOP_TO_BOTTOM = auto()
    TOP_TO_BOTTOM_LEFT_TO_RIGHT = auto()
    TOP_TO_BOTTOM_RIGHT_TO_LEFT = auto()


_ELEMENT_ORDERING_FUNCTIONS: Dict[ElementOrdering, Callable[[List], List]] = {
    ElementOrdering.LEFT_TO_RIGHT_TOP_TO_BOTTOM: lambda elements: sorted(
        elements, key=lambda elem: (-elem.y0, elem.x0)
    ),
    ElementOrdering.RIGHT_TO_LEFT_TOP_TO_BOTTOM: lambda elements: sorted(
        elements, key=lambda elem: (-elem.y0, -elem.x0)
    ),
    ElementOrdering.TOP_TO_BOTTOM_LEFT_TO_RIGHT: lambda elements: sorted(
        elements, key=lambda elem: (elem.x0, -elem.y0)
    ),
    ElementOrdering.TOP_TO_BOTTOM_RIGHT_TO_LEFT: lambda elements: sorted(
        elements, key=lambda elem: (-elem.x0, -elem.y0)
    ),
}


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
        page_number (int): The page number.
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

        Returns:
            ElementList: All the elements on the page.
        """
        return self.document.elements.between(
            self.start_element, self.end_element, inclusive=True
        )


class PDFElement:
    """
    A representation of a single element within the pdf.

    You should not instantiate this yourself, but should let the `PDFDocument` do this.

    Args:
        document (PDFDocument): A reference to the `PDFDocument`.
        element (LTComponent): A PDF Miner LTComponent.
        index (int): The index of the element within the document.
        page_number (int): The page number that the element is on.
        font_size_precision (int): How much rounding to apply to the font size. The font
            size will be rounded to this many decimal places.

    Attributes:
        original_element (LTComponent): A reference to the original PDF Miner element.
        tags (set[str]): A list of tags that have been added to the element.
        bounding_box (BoundingBox): The box representing the location of the element.
    """

    document: "PDFDocument"
    original_element: "LTComponent"
    tags: Set[str]
    bounding_box: BoundingBox
    _index: int
    __font_name: Optional[str] = None
    __font_size: Optional[float] = None
    __font_size_precision: int
    __font: Optional[str] = None
    __page_number: int

    def __init__(
        self,
        document: "PDFDocument",
        element: "LTComponent",
        index: int,
        page_number: int,
        font_size_precision: int = 1,
    ):
        self.document = document
        self.original_element = element
        self._index = index
        self.__page_number = page_number
        self.__font_size_precision = font_size_precision

        self.tags = set()

        self.bounding_box = BoundingBox(
            x0=element.x0, x1=element.x1, y0=element.y0, y1=element.y1
        )

    @property
    def page_number(self) -> int:
        """
        The page_number of the element in the document.

        Returns:
            int: The page number of the element.
        """
        return self.__page_number

    @property
    def font_name(self) -> str:
        """
        The name of the font.

        This will be taken from the pdf itself, using the most common font within all
        the characters in the element.

        Returns:
            str: The font name of the element.
        """
        if self.__font_name is not None:
            return self.__font_name

        counter = Counter(
            (
                character.fontname
                for line in self.original_element
                for character in line
                if hasattr(character, "fontname")
            )
        )
        self.__font_name = counter.most_common(1)[0][0]
        return self.__font_name

    @property
    def font_size(self) -> float:
        """
        The size of the font.

        This will be taken from the pdf itself, using the most common size within all
        the characters in the element.

        Returns:
            float: The font size of the element, rounded to the font_size_precision of
                the document.
        """
        if self.__font_size is not None:
            return self.__font_size

        counter = Counter(
            (
                character.height
                for line in self.original_element
                for character in line
                if hasattr(character, "height")
            )
        )
        self.__font_size = round(
            counter.most_common(1)[0][0], self.__font_size_precision
        )
        return self.__font_size

    @property
    def font(self) -> str:
        """
        The name and size of the font, separated by a comma with no spaces.

        This will be taken from the pdf itself, using the first character in the
        element.

        If you have provided a font_mapping, this is the string you should map. If
        the string is mapped in your font_mapping then the mapped value will be
        returned. font_mapping can have regexes as keys.

        Returns:
            str: The font of the element.
        """
        if self.__font is not None:
            return self.__font

        font = f"{self.font_name},{self.font_size}"
        if self.document._font_mapping_is_regex:
            for pattern, font_name in self.document._font_mapping.items():
                if re.match(pattern, font, self.document._regex_flags):
                    self.__font = font_name
                    return self.__font
        self.__font = self.document._font_mapping.get(font) or font
        return self.__font

    @property
    def ignored(self) -> bool:
        """
        A flag specifying whether the element has been ignored.
        """
        return self._index in self.document._ignored_indexes

    def add_tag(self, new_tag: str):
        """
        Adds the `new_tag` to the tags set.

        Args:
            new_tag (str): The tag you would like to add.
        """
        self.tags.add(new_tag)

    def entirely_within(self, bounding_box: BoundingBox) -> bool:
        """
        Whether the entire element is within the bounding box.

        Args:
            bounding_box (BoundingBox): The bounding box to check whether the element
                is within.

        Returns:
            bool: True if the element is entirely contained within the bounding box.
        """
        return all(
            [
                self.bounding_box.x0 >= bounding_box.x0,
                self.bounding_box.x1 <= bounding_box.x1,
                self.bounding_box.y0 >= bounding_box.y0,
                self.bounding_box.y1 <= bounding_box.y1,
            ]
        )

    def ignore(self):
        """
        Marks the element as ignored.

        The element will no longer be returned in any newly instantiated `ElementList`.
        Note that this includes calling any new filter functions on an existing
        `ElementList`, since doing so always returns a new `ElementList`.
        """
        self.document._ignored_indexes.add(self._index)

    def partially_within(self, bounding_box: BoundingBox) -> bool:
        """
        Whether any part of the element is within the bounding box.

        Args:
            bounding_box (BoundingBox): The bounding box to check whether the element
                is partially within.

        Returns:
            bool: True if any part of the element is within the bounding box.
        """
        return all(
            [
                bounding_box.x0 <= self.bounding_box.x1,
                bounding_box.x1 >= self.bounding_box.x0,
                bounding_box.y0 <= self.bounding_box.y1,
                bounding_box.y1 >= self.bounding_box.y0,
            ]
        )

    def text(self, stripped: bool = True) -> str:
        """
        The text contained in the element.

        Args:
            stripped (bool, optional): Whether to strip the text of the element.
                Default: True.

        Returns:
            str: The text contained in the element.
        """
        txt = self.original_element.get_text()
        return txt.strip() if stripped else txt

    def __repr__(self):
        return (
            f"<PDFElement tags: {self.tags}, font: '{self.font}'"
            f"{', ignored' if self.ignored else ''}>"
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
        pages (dict[int, Page]): A dictionary mapping page numbers (int) to pages, where
            pages are a `Page` namedtuple (containing a width, height and a list of
            elements from PDFMiner).
        pdf_file_path (str, optional): A file path to the PDF file. This is optional,
            and is only used to display your pdf as a background image when using the
            visualise functions.
        font_mapping (dict, optional): `PDFElement`s have a `font` attribute, and the
            font is taken from the PDF. You can map these fonts to instead use your own
            internal font names by providing a font_mapping. This is a dictionary with
            keys being the original font (including font size) and values being your
            new names.
        font_mapping_is_regex (bool, optional): Indicates whether font_mapping keys
            should be considered as regexes. In this case all the fonts will be matched
            with the regexes. It is only relevant if font_mapping is not None.
            Default: False.
        regex_flags (str, optional): Regex flags compatible with the re module.
                Default: 0.
        font_size_precision (int): How much rounding to apply to the font size. The font
            size will be rounded to this many decimal places.
        element_ordering (ElementOrdering or callable, optional): An ordering function
            for the elements. Either a member of the ElementOrdering Enum, or a callable
            which takes a list of elements and returns an ordered list of elements. This
            will be called separately for each page. Note that the elements in this case
            will be PDFMiner elements, and not PDFElements from this package.

    Attributes:
        number_of_pages (int): The total number of pages in the document.
        page_numbers (list(int)): A list of available page numbers.
        sectioning: Gives access to the sectioning utilities. See the documentation for
            the `Sectioning` class.
    """

    number_of_pages: int
    page_numbers: List[int]
    sectioning: "Sectioning"
    # _element_list will contain all elements, sorted according to element_ordering
    # (default left to right, top to bottom).
    _element_list: List[PDFElement]
    # _element_indexes_by_font will be a caching of fonts to elements indexes but it
    # will be built as needed (while filtering by fonts), not on document load.
    _element_indexes_by_font: Dict[str, Set[int]]
    _ignored_indexes: Set[int]
    _font_mapping: Dict[str, str]
    _font_mapping_is_regex: bool
    _regex_flags: Union[int, re.RegexFlag]
    _pdf_file_path: Optional[str]
    __pages: Dict[int, PDFPage]

    def __init__(
        self,
        pages: Dict[int, "Page"],
        pdf_file_path: Optional[str] = None,
        font_mapping: Optional[Dict[str, str]] = None,
        font_mapping_is_regex: bool = False,
        regex_flags: Union[int, re.RegexFlag] = 0,
        font_size_precision: int = 1,
        element_ordering: Union[
            ElementOrdering, Callable[[List], List]
        ] = ElementOrdering.LEFT_TO_RIGHT_TOP_TO_BOTTOM,
    ):
        self.sectioning = Sectioning(self)
        self._element_list = []
        self._element_indexes_by_font = defaultdict(set)
        self._font_mapping = font_mapping if font_mapping is not None else {}
        self._font_mapping_is_regex = font_mapping_is_regex
        self._regex_flags = regex_flags
        self._ignored_indexes = set()
        self.__pages = {}
        idx = 0
        for page_number, page in sorted(pages.items()):
            first_element = None
            if isinstance(element_ordering, ElementOrdering):
                sort_func = _ELEMENT_ORDERING_FUNCTIONS[element_ordering]
            else:
                sort_func = element_ordering
            for element in sort_func(page.elements):
                pdf_element = PDFElement(
                    document=self,
                    element=element,
                    index=idx,
                    page_number=page_number,
                    font_size_precision=font_size_precision,
                )
                self._element_list.append(pdf_element)
                idx += 1
                if first_element is None:
                    first_element = pdf_element

            if first_element is None:
                raise NoElementsOnPageError(
                    f"No elements on page {page_number}, please exclude this page"
                )

            self.__pages[page_number] = PDFPage(
                document=self,
                width=page.width,
                height=page.height,
                page_number=page_number,
                start_element=first_element,
                end_element=pdf_element,
            )

        self._pdf_file_path = pdf_file_path
        self.number_of_pages = len(pages)
        self.page_numbers = [page.page_number for page in self.pages]

    @property
    def elements(self) -> "ElementList":
        """
        An ElementList containing all elements in the document.

        Returns:
            ElementList: All elements in the document.
        """
        return ElementList(self)

    @property
    def pages(self) -> List["PDFPage"]:
        """
        A list of all pages in the document.

        Returns:
            list[PDFPage]: All pages in the document.
        """
        return [self.__pages[page_number] for page_number in sorted(self.__pages)]

    @property
    def fonts(self) -> Set[str]:
        """
        A set of all the fonts in the document.

        Returns:
            set[str]: All the fonts in the document.
        """
        return set(element.font for element in self.elements)

    def get_page(self, page_number: int) -> "PDFPage":
        """
        Returns the `PDFPage` for the specified `page_number`.

        Args:
            page_number (int): The page number.

        Raises:
            PageNotFoundError: If `page_number` was not found.

        Returns:
            PDFPage: The requested page.
        """
        try:
            return self.__pages[page_number]
        except KeyError as err:
            raise PageNotFoundError(f"Could not find page {page_number}") from err

    def _element_indexes_with_fonts(self, *fonts: str) -> Set[int]:
        """
        Returns all the indexes of elements with given fonts.
        For internal use only, used to cache fonts. If you want to filter by fonts you
        should use elements.filter_by_fonts instead.

        Args:
            *fonts (str): The fonts to filter for.

        Returns:
            Set[int]: The elements indexes.
        """
        non_cached_fonts = [
            font for font in fonts if font not in self._element_indexes_by_font.keys()
        ]
        if non_cached_fonts:
            # If we don't have cached elements for any of the required fonts, build
            # the cache for the non cached fonts.
            for element in self._element_list:
                if element.font not in non_cached_fonts:
                    continue

                self._element_indexes_by_font[element.font].add(element._index)

        # Returns elements based on the caching of fonts to elements indexes.
        return set(
            chain.from_iterable(
                [
                    indexes
                    for font, indexes in self._element_indexes_by_font.items()
                    if font in fonts
                ]
            )
        )
