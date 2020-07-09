from typing import (
    overload,
    Union,
    Set,
    FrozenSet,
    Optional,
    Iterable,
    Iterator,
    TYPE_CHECKING,
)

import re

from .common import BoundingBox
from .exceptions import (
    ElementOutOfRangeError,
    NoElementFoundError,
    MultipleElementsFoundError,
    SectionNotFoundError,
)

if TYPE_CHECKING:
    from .components import PDFDocument, PDFElement


class ElementIterator(Iterator):
    index: int
    document: "PDFDocument"

    def __init__(self, element_list: "ElementList"):
        self.index = 0
        self.document = element_list.document
        self.indexes = iter(sorted(element_list.indexes))

    def __next__(self):
        index = next(self.indexes)
        return self.document._element_list[index]


class ElementList(Iterable):
    """
    Used to represent a list of elements, and to enable filtering of those elements.

    Any time you have a group of elements, for example pdf_document.elements or
    page.elements, you will get an `ElementList`. You can iterate through this, and also
    access specific elements. On top of this, there are lots of methods which you can
    use to further filter your elements. Since all of these methods return a new
    ElementList, you can chain these operations.

    Internally, we keep a set of indexes corresponding to the PDFElements in the
    document. This means you can treat ElementLists like sets to combine different
    ElementLists together.

    We often implement pluralised versions of methods, which is a shortcut to applying
    the or operator | to multiple ElementLists with the singular version applied, for
    example `foo.filter_by_tags("bar", "baz")` is the same as
    `foo.filter_by_tag("bar") | foo.filter_by_tag("baz")`.

    Similarly, chaining two filter commands is the same as applying the & operator,
    for example `foo.filter_by_tag("bar").filter_by_tag("baz")` is the same as
    `foo.filter_by_tag("bar") & foo.filter_by_tag("baz")`. Note that this is not the
    case for methods which do not filter, e.g. `add_element`.

    Ignored elements will be excluded on instantiation. Each time you chain a new filter
    a new ElementList is returned. Note this will remove newly-ignored elements.

    Note:
        As ElementList is implemented using sets internally, you will not be able to
        have an element in an ElementList multiple times.

    Args:
        document (PDFDocument): A reference to the PDF document
        indexes (set, optional): A set (or frozenset) of element indexes. Defaults to
            all elements in the document.

    Attributes:
        document (PDFDocument): A reference to the PDF document.
        indexes (set, optional): A frozenset of element indexes.
    """

    document: "PDFDocument"
    indexes: Union[Set[int], FrozenSet[int]]

    def __init__(
        self,
        document: "PDFDocument",
        indexes: Optional[Union[Set[int], FrozenSet[int]]] = None,
    ):
        self.document = document
        if indexes is not None:
            self.indexes = frozenset(indexes)
        else:
            self.indexes = frozenset(range(0, len(document._element_list)))
        self.indexes = self.indexes - self.document._ignored_indexes

    def add_tag_to_elements(self, tag: str) -> None:
        """
        Adds a tag to all elements in the list.

        Args:
            tag (str): The tag you would like to add.
        """
        for element in self:
            element.add_tag(tag)

    def filter_by_tag(self, tag: str) -> "ElementList":
        """
        Filter for elements containing only the given tag.

        Args:
            tag (str): The tag to filter for.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes = set(element._index for element in self if tag in element.tags)
        return ElementList(self.document, new_indexes)

    def filter_by_tags(self, *tags: str) -> "ElementList":
        """
        Filter for elements containing any of the given tags.

        Args:
            *tags (str): The tags to filter for.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes = set(
            element._index
            for element in self
            if any(tag in element.tags for tag in tags)
        )
        return ElementList(self.document, new_indexes)

    def filter_by_text_equal(self, text: str, stripped: bool = True) -> "ElementList":
        """
        Filter for elements whose text is exactly the given string.

        Args:
            text (str): The text to filter for.
            stripped (bool, optional): Whether to strip the text of the element before
                comparison. Default: True.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes = set(
            element._index for element in self if element.text(stripped) == text
        )

        return ElementList(self.document, new_indexes)

    def filter_by_text_contains(self, text: str) -> "ElementList":
        """
        Filter for elements whose text contains the given string.

        Args:
            text (str): The text to filter for.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes = set(element._index for element in self if text in element.text())
        return ElementList(self.document, new_indexes)

    def filter_by_regex(
        self,
        regex: str,
        regex_flags: Union[int, re.RegexFlag] = 0,
        stripped: bool = True,
    ):
        """
        Filter for elements given a regular expression.

        Args:
            regex (str): The regex to filter for.
            regex_flags (str, optional): Regex flags compatible with the re module.
                Default: 0.
            stripped (bool, optional): Whether to strip the text of the element before
                comparison. Default: True.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes = set(
            element._index
            for element in self
            if re.match(regex, element.text(stripped), flags=regex_flags)
        )

        return ElementList(self.document, new_indexes)

    def filter_by_font(self, font: str) -> "ElementList":
        """
        Filter for elements containing only the given font.

        Args:
            font (str): The font to filter for.

        Returns:
            ElementList: The filtered list.
        """
        return self.filter_by_fonts(font)

    def filter_by_fonts(self, *fonts: str) -> "ElementList":
        """
        Filter for elements containing only the given font.

        Args:
            *fonts (str): The fonts to filter for.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes = self.indexes & self.document._element_indexes_with_fonts(*fonts)
        return ElementList(self.document, new_indexes)

    def filter_by_page(self, page_number: int) -> "ElementList":
        """
        Filter for elements on the given page.

        Args:
            page (int): The page to filter for.

        Returns:
            ElementList: The filtered list.
        """
        page = self.document.get_page(page_number)
        new_indexes = set(element._index for element in page.elements)
        return self.__intersect_indexes_with_self(new_indexes)

    def filter_by_pages(self, *page_numbers: int) -> "ElementList":
        """
        Filter for elements on any of the given pages.

        Args:
            *pages (int): The pages to filter for.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes: Set[int] = set()
        for page_number in page_numbers:
            page = self.document.get_page(page_number)
            new_indexes |= set(element._index for element in page.elements)
        return self.__intersect_indexes_with_self(new_indexes)

    def filter_by_section_name(self, section_name: str) -> "ElementList":
        """
        Filter for elements within any section with the given name.

        See the sectioning documentation for more details.

        Args:
            section_name (str): The section name to filter for.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes: Set[int] = set()
        for section in self.document.sectioning.get_sections_with_name(section_name):
            new_indexes |= set(element._index for element in section.elements)
        return self.__intersect_indexes_with_self(new_indexes)

    def filter_by_section_names(self, *section_names: str) -> "ElementList":
        """
        Filter for elements within any section with any of the given names.

        See the sectioning documentation for more details.

        Args:
            *section_names (str): The section names to filter for.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes: Set[int] = set()
        for section_name in section_names:
            for section in self.document.sectioning.get_sections_with_name(
                section_name
            ):
                new_indexes |= set(element._index for element in section.elements)
        return self.__intersect_indexes_with_self(new_indexes)

    def filter_by_section(self, section_str: str) -> "ElementList":
        """
        Filter for elements within the given section.

        See the sectioning documentation for more details.

        Args:
            section_name (str): The section to filter for.

        Note:
            You need to specify an exact section, not just the name (i.e. "foo_0" not
            just "foo").

        Returns:
            ElementList: The filtered list.
        """
        try:
            section = self.document.sectioning.get_section(section_str)
            new_indexes = set(element._index for element in section.elements)
            return self.__intersect_indexes_with_self(new_indexes)
        except SectionNotFoundError:
            # Section doesn't exist - return empty ElementList.
            return self.__intersect_indexes_with_self(set())

    def filter_by_sections(self, *section_strs: str) -> "ElementList":
        """
        Filter for elements within any of the given sections.

        See the sectioning documentation for more details.

        Args:
            *section_names (str): The sections to filter for.

        Note:
            You need to specify an exact section, not just the name (i.e. "foo_0" not
            just "foo").

        Returns:
            ElementList: The filtered list.
        """
        new_indexes: Set[int] = set()
        for section_str in section_strs:
            try:
                section = self.document.sectioning.sections_dict[section_str]
                new_indexes |= set(element._index for element in section.elements)
            except SectionNotFoundError:
                # This section doesn't exist. That's fine, keep checking the other ones.
                pass
        return self.__intersect_indexes_with_self(new_indexes)

    def ignore_elements(self) -> None:
        """
        Marks all the elements in the ElementList as ignored.
        """
        self.document._ignored_indexes = self.document._ignored_indexes.union(
            self.indexes
        )

    def to_the_right_of(
        self, element: "PDFElement", inclusive: bool = False, tolerance: float = 0.0
    ) -> "ElementList":
        """
        Filter for elements which are to the right of the given element.

        If you draw a box from the right hand edge of the element to the right hand
        side of the page, all elements which are partially within this box are returned.

        Note:
            By "to the right of" we really mean "directly to the right of", i.e. the
            returned elements all have at least some part which is vertically aligned
            with the specified element.

        Note:
            Technically the element you specify will satisfy the condition, but we
            assume you do not want that element returned. If you do, you can pass
            `inclusive=True`.

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.
            tolerance (int, optional): To be counted as to the right, the elements must
                overlap by at least `tolerance` on the Y axis. Tolerance is capped at
                half the height of the element. Default 0.

        Returns:
            ElementList: The filtered list.
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        tolerance = min(element.bounding_box.height / 2, tolerance)
        bounding_box = BoundingBox(
            element.bounding_box.x1,
            page.width,
            element.bounding_box.y0 + tolerance,
            element.bounding_box.y1 - tolerance,
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if not inclusive:
            results = results.remove_element(element)
        return results

    def to_the_left_of(
        self, element: "PDFElement", inclusive: bool = False, tolerance: float = 0.0
    ) -> "ElementList":
        """
        Filter for elements which are to the left of the given element.


        If you draw a box from the left hand edge of the element to the left hand
        side of the page, all elements which are partially within this box are returned.

        Note:
            By "to the left of" we really mean "directly to the left of", i.e. the
            returned elements all have at least some part which is vertically aligned
            with the specified element.

        Note:
            Technically the element you specify will satisfy the condition, but we
            assume you do not want that element returned. If you do, you can pass
            `inclusive=True`.

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.
            tolerance (int, optional): To be counted as to the left, the elements must
                overlap by at least `tolerance` on the Y axis. Tolerance is capped at
                half the height of the element. Default 0.


        Returns:
            ElementList: The filtered list.
        """
        page_number = element.page_number
        tolerance = min(element.bounding_box.height / 2, tolerance)
        bounding_box = BoundingBox(
            0,
            element.bounding_box.x0,
            element.bounding_box.y0 + tolerance,
            element.bounding_box.y1 - tolerance,
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if not inclusive:
            results = results.remove_element(element)
        return results

    def below(
        self,
        element: "PDFElement",
        inclusive: bool = False,
        all_pages: bool = False,
        tolerance: float = 0.0,
    ) -> "ElementList":
        """
        Returns all elements which are below the given element.

        If you draw a box from the bottom edge of the element to the bottom of the page,
        all elements which are partially within this box are returned. By default, only
        elements on the same page as the given element are included, but you can pass
        `inclusive=True` to also include the pages which come after (and so are below)
        the page containing the given element.

        Note:
            By "below" we really mean "directly below", i.e. the returned elements all
            have at least some part which is horizontally aligned with the specified
            element.

        Note:
            Technically the element you specify will satisfy the condition, but we
            assume you do not want that element returned. If you do, you can pass
            `inclusive=True`.

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.
            all_pages (bool, optional): Whether to included pages other than the page
                which the element is on.
            tolerance (int, optional): To be counted as below, the elements must
                overlap by at least `tolerance` on the X axis. Tolerance is capped at
                half the width of the element. Default 0.

        Returns:
            ElementList: The filtered list.
        """
        page_number = element.page_number
        tolerance = min(element.bounding_box.width / 2, tolerance)
        bounding_box = BoundingBox(
            element.bounding_box.x0 + tolerance,
            element.bounding_box.x1 - tolerance,
            0,
            element.bounding_box.y0,
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if all_pages:
            for page in self.document.pages:
                if page.page_number <= page_number:
                    continue
                # We're on a page which is located below our element, so the bounding
                # box should be the length of the entire page.
                bounding_box = BoundingBox(
                    element.bounding_box.x0 + tolerance,
                    element.bounding_box.x1 - tolerance,
                    0,
                    page.height,
                )
                results = results | self.filter_partially_within_bounding_box(
                    bounding_box, page.page_number
                )
        if not inclusive:
            results = results.remove_element(element)
        return results

    def above(
        self,
        element: "PDFElement",
        inclusive: bool = False,
        all_pages: bool = False,
        tolerance: float = 0.0,
    ) -> "ElementList":
        """
        Returns all elements which are above the given element.

        If you draw a box from the bottom edge of the element to the bottom of the page,
        all elements which are partially within this box are returned. By default, only
        elements on the same page as the given element are included, but you can pass
        `inclusive=True` to also include the pages which come before (and so are above)
        the page containing the given element.

        Note:
            By "above" we really mean "directly above", i.e. the returned elements all
            have at least some part which is horizontally aligned with the specified
            element.

        Note:
            Technically the element you specify will satisfy the condition, but we
            assume you do not want that element returned. If you do, you can pass
            `inclusive=True`.

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.
            all_pages (bool, optional): Whether to included pages other than the page
                which the element is on.
            tolerance (int, optional): To be counted as above, the elements must
                overlap by at least `tolerance` on the X axis. Tolerance is capped at
                half the width of the element. Default 0.

        Returns:
            ElementList: The filtered list.
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        tolerance = min(element.bounding_box.width / 2, tolerance)
        bounding_box = BoundingBox(
            element.bounding_box.x0 + tolerance,
            element.bounding_box.x1 - tolerance,
            element.bounding_box.y1,
            page.height,
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if all_pages:
            for page in self.document.pages:
                if page.page_number >= page_number:
                    continue
                # We're on a page which is located above our element, so the bounding
                # box should be the length of the entire page.
                bounding_box = BoundingBox(
                    element.bounding_box.x0 + tolerance,
                    element.bounding_box.x1 - tolerance,
                    0,
                    page.height,
                )
                results = results | self.filter_partially_within_bounding_box(
                    bounding_box, page.page_number
                )
        if not inclusive:
            results = results.remove_element(element)
        return results

    def vertically_in_line_with(
        self,
        element: "PDFElement",
        inclusive: bool = False,
        all_pages: bool = False,
        tolerance: float = 0.0,
    ) -> "ElementList":
        """
        Returns all elements which are vertically in line with the
        given element.

        If you extend the left and right edges of the element to the top and bottom of
        the page, all elements which are partially within this box are returned. By
        default, only elements on the same page as the given element are included, but
        you can pass `inclusive=True` to include all pages.

        This is equivalent to doing `foo.above(...) | foo.below(...)`.

        Note:
            Technically the element you specify will satisfy the condition, but we
            assume you do not want that element returned. If you do, you can pass
            `inclusive=True`.

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.
            all_pages (bool, optional): Whether to included pages other than the page
                which the element is on.
            tolerance (int, optional): To be counted as in line with, the elements must
                overlap by at least `tolerance` on the X axis. Tolerance is capped at
                half the width of the element. Default 0.

        Returns:
            ElementList: The filtered list.
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        tolerance = min(element.bounding_box.width / 2, tolerance)
        bounding_box = BoundingBox(
            element.bounding_box.x0 + tolerance,
            element.bounding_box.x1 - tolerance,
            0,
            page.height,
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if all_pages:
            for page_num in range(self[0].page_number, self[-1].page_number + 1):
                page = self.document.get_page(page_num)
                if page.page_number == page_number:
                    # Already handled page containing element
                    continue
                bounding_box = BoundingBox(
                    element.bounding_box.x0 + tolerance,
                    element.bounding_box.x1 - tolerance,
                    0,
                    page.height,
                )
                results = results | self.filter_partially_within_bounding_box(
                    bounding_box, page.page_number
                )

        if not inclusive:
            results = results.remove_element(element)
        return results

    def horizontally_in_line_with(
        self, element: "PDFElement", inclusive: bool = False, tolerance: float = 0.0
    ) -> "ElementList":
        """
        Returns all elements which are horizontally in line with the given element.

        If you extend the top and bottom edges of the element to the left and right of
        the page, all elements which are partially within this box are returned.

        This is equivalent to doing
        `foo.to_the_left_of(...) | foo.to_the_right_of(...)`.

        Note:
            Technically the element you specify will satisfy the condition, but we
            assume you do not want that element returned. If you do, you can pass
            `inclusive=True`.

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.
            tolerance (int, optional): To be counted as in line with, the elements must
                overlap by at least `tolerance` on the Y axis. Tolerance is capped at
                half the width of the element. Default 0.

        Returns:
            ElementList: The filtered list.
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        tolerance = min(element.bounding_box.height / 2, tolerance)
        bounding_box = BoundingBox(
            0,
            page.width,
            element.bounding_box.y0 + tolerance,
            element.bounding_box.y1 - tolerance,
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if not inclusive:
            results = results.remove_element(element)
        return results

    def filter_partially_within_bounding_box(
        self, bounding_box: BoundingBox, page_number: int
    ) -> "ElementList":
        """
        Returns all elements on the given page which are partially within the given box.

        Args:
            bounding_box (BoundingBox): The bounding box to filter within.
            page_number (int): The page which you'd like to filter within the box.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes: Set[int] = set()
        for elem in self.filter_by_page(page_number):
            if elem.partially_within(bounding_box):
                new_indexes.add(elem._index)
        return self.__intersect_indexes_with_self(new_indexes)

    def before(self, element: "PDFElement", inclusive: bool = False) -> "ElementList":
        """
        Returns all elements before the specified element.

        By before, we mean preceding elements according to their index. The PDFDocument
        will order elements according to the specified element_ordering (which defaults
        to left to right, top to bottom).

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes = set(range(0, element._index))
        if inclusive:
            new_indexes.add(element._index)
        return self.__intersect_indexes_with_self(new_indexes)

    def after(self, element: "PDFElement", inclusive: bool = False) -> "ElementList":
        """
        Returns all elements after the specified element.

        By after, we mean succeeding elements according to their index. The PDFDocument
        will order elements according to the specified element_ordering (which defaults
        to left to right, top to bottom).

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes = set(range(element._index + 1, max(self.indexes) + 1))
        if inclusive:
            new_indexes.add(element._index)
        return self.__intersect_indexes_with_self(new_indexes)

    def between(
        self,
        start_element: "PDFElement",
        end_element: "PDFElement",
        inclusive: bool = False,
    ):
        """
        Returns all elements between the start and end elements.

        This is done according to the element indexes. The PDFDocument will order
        elements according to the specified element_ordering (which defaults
        to left to right, top to bottom).

        This is the same as applying `before` with `start_element` and `after` with
        `end_element`.

        Args:
            start_element (PDFElement): Returned elements will be after this element.
            end_element (PDFElement): Returned elements will be before this element.
            inclusive (bool, optional): Whether the include `start_element` and
                `end_element` in the returned results. Default: False.

        Returns:
            ElementList: The filtered list.
        """
        new_indexes = set(range(start_element._index + 1, end_element._index))
        if inclusive:
            new_indexes = new_indexes.union([start_element._index, end_element._index])
        return self.__intersect_indexes_with_self(new_indexes)

    def extract_single_element(self) -> "PDFElement":
        """
        Returns only element in the ElementList, provided there is only one element.

        This is mainly for convenience, when you think you've filtered down to a single
        element and you would like to extract said element.

        Raises:
            NoElementFoundError: If there are no elements in the ElementList
            MultipleElementsFoundError: If there is more than one element in the
                ElementList

        Returns:
            PDFElement: The single element remaining in the list.
        """
        if len(self.indexes) == 0:
            raise NoElementFoundError("There are no elements in the ElementList")
        if len(self.indexes) > 1:
            raise MultipleElementsFoundError(
                f"There are {len(self.indexes)} elements in the ElementList"
            )

        return self.document._element_list[list(self.indexes)[0]]

    def add_element(self, element: "PDFElement") -> "ElementList":
        """
        Explicitly adds the element to the ElementList.

        Note:
            If the element is already in the ElementList, this does nothing.

        Args:
            element (PDFElement): The element to add.

        Returns:
            ElementList: A new list with the additional element.
        """
        return ElementList(self.document, self.indexes | set([element._index]))

    def add_elements(self, *elements: "PDFElement") -> "ElementList":
        """
        Explicitly adds the elements to the ElementList.

        Note:
            If the elements is already in the ElementList, this does nothing.

        Args:
            *elements (PDFElement): The elements to add.

        Returns:
            ElementList: A new list with the additional elements.
        """
        return ElementList(
            self.document, self.indexes | set([element._index for element in elements])
        )

    def remove_element(self, element: "PDFElement") -> "ElementList":
        """
        Explicitly removes the element from the ElementList.

        Note:
            If the element is not in the ElementList, this does nothing.

        Args:
            element (PDFElement): The element to remove.

        Returns:
            ElementList: A new list without the element.
        """
        return ElementList(self.document, self.indexes - set([element._index]))

    def remove_elements(self, *elements: "PDFElement") -> "ElementList":
        """
        Explicitly removes the elements from the ElementList.

        Note:
            If the elements are not in the ElementList, this does nothing.

        Args:
            *elements (PDFElement): The elements to remove.

        Returns:
            ElementList: A new list without the elements.
        """
        return ElementList(
            self.document, self.indexes - set(element._index for element in elements)
        )

    def move_forwards_from(
        self, element: "PDFElement", count: int = 1, capped: bool = False
    ) -> "PDFElement":
        """
        Returns the element in the element list obtained by moving forwards from
        `element` by `count`.

        Args:
            element (PDFElement): The element to start at.
            count (int, optional): How many elements to move from `element`. The default
                of 1 will move forwards by one element. Passing 0 will simply return the
                element itself. You can also pass negative integers to move backwards.
            capped (bool, optional): By default (False), if the count is high enough
                that we try to move out of range of the list, an exception will be
                raised. Passing `capped=True` will change this behaviour to instead
                return the element at the start or end of the list.

        Raises:
            ElementOutOfRangeError: If the count is large (or large-negative) enough
                that we reach the end (or start) of the list. Only happens when
                capped=False.
        """
        indexes = sorted(self.indexes)
        new_index = indexes.index(element._index) + count
        if new_index < 0 or new_index >= len(indexes):
            # Out of range. We could simply catch the index error for large new_index,
            # but we have to handle the negative case like this anyway, so might as well
            # do both cases while we're at it.
            if capped:
                new_index = max(min(new_index, len(indexes) - 1), 0)
                element_index = indexes[new_index]
                return self.document._element_list[element_index]
            raise ElementOutOfRangeError(
                f"Requested element is {'before' if new_index < 0 else 'after'} the "
                f"{'start' if new_index < 0 else 'end'} of the ElementList"
            )

        # We avoid just returning self[new_index] here since getitem will do an
        # additional sorted(self.indexes), which we have already computed here.
        element_index = indexes[new_index]
        return self.document._element_list[element_index]

    def move_backwards_from(
        self, element: "PDFElement", count: int = 1, capped: bool = False
    ) -> "PDFElement":
        """
        Returns the element in the element list obtained by moving backwards from
        `element` by `count`.

        Args:
            element (PDFElement): The element to start at.
            count (int, optional): How many elements to move from `element`. The default
                of 1 will move backwards by one element. Passing 0 will simply return
                the element itself. You can also pass negative integers to move
                forwards.
            capped (bool, optional): By default (False), if the count is high enough
                that we try to move out of range of the list, an exception will be
                raised. Passing `capped=True` will change this behaviour to instead
                return the element at the start or end of the list.

        Raises:
            ElementOutOfRangeError: If the count is large (or large-negative) enough
                that we reach the start (or end) of the list. Only happens when
                capped=False.
        """
        return self.move_forwards_from(element, count=-count, capped=capped)

    def __intersect_indexes_with_self(self, new_indexes: Set[int]) -> "ElementList":
        return self & ElementList(self.document, new_indexes)

    def __iter__(self) -> ElementIterator:
        """
        Returns an ElementIterator class that allows iterating through elements.

        Elements will be returned in order of the elements in the document,
        left-to-right, top-to-bottom (the same as you read).
        """
        return ElementIterator(self)

    def __contains__(self, element: "PDFElement") -> bool:
        """
        Returns True if the element is in the ElementList, otherwise False.
        """
        return element._index in self.indexes

    def __repr__(self):
        return f"<ElementList of {len(self.indexes)} elements>"

    @overload
    def __getitem__(self, key: int) -> "PDFElement":
        pass  # This is for type checking only

    @overload
    def __getitem__(self, key: slice) -> "ElementList":
        pass  # This is for type checking only

    def __getitem__(self, key: Union[int, slice]) -> Union["PDFElement", "ElementList"]:
        """
        Returns the element in position `key` of the ElementList if an int is given, or
        returns a new ElementList if a slice is given.

        Elements are ordered by their original positions in the document, which is
        left-to-right, top-to-bottom (the same you you read).
        """
        if isinstance(key, slice):
            new_indexes = set(sorted(self.indexes)[key])
            return ElementList(self.document, new_indexes)
        element_index = sorted(self.indexes)[key]
        return self.document._element_list[element_index]

    def __eq__(self, other: object) -> bool:
        """
        Returns True if the two ElementLists contain the same elements from the same
        document.
        """
        if not isinstance(other, ElementList):
            raise NotImplementedError(f"Can't compare ElementList with {type(other)}")
        return (
            self.indexes == other.indexes
            and self.document == other.document
            and self.__class__ == other.__class__
        )

    def __hash__(self):
        return hash(hash(self.indexes) + hash(self.document))

    def __len__(self):
        """
        Returns the number of elements in the ElementList.
        """
        return len(self.indexes)

    def __sub__(self, other: "ElementList") -> "ElementList":
        """
        Returns an ElementList of elements that are in the first ElementList but not in
        the second.
        """
        return ElementList(self.document, self.indexes - other.indexes)

    def __or__(self, other: "ElementList") -> "ElementList":
        """
        Returns an ElementList of elements that are in either ElementList
        """
        return ElementList(self.document, self.indexes | other.indexes)

    def __xor__(self, other: "ElementList") -> "ElementList":
        """
        Returns an ElementList of elements that are in either ElementList, but not both.
        """
        return ElementList(self.document, self.indexes ^ other.indexes)

    def __and__(self, other: "ElementList") -> "ElementList":
        """
        Returns an ElementList of elements that are in both ElementList
        """
        return ElementList(self.document, self.indexes & other.indexes)
