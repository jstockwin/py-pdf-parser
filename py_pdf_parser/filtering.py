from typing import Union, Set, FrozenSet, Optional, Iterable, Iterator, TYPE_CHECKING

from .common import BoundingBox
from .exceptions import NoElementFoundError, MultipleElementsFoundError

if TYPE_CHECKING:
    from .components import PDFDocument, PDFElement


class ElementIterator(Iterator):
    """
    Iterates through the elements of an ElementList.

    Elements will be returned in order of the elements in the document, left-to-right,
    top-to-bottom (the same as you read).
    """

    index: int
    document: "PDFDocument"

    def __init__(self, element_list: "ElementList"):
        self.index = 0
        self.document = element_list.document
        self.indexes = iter(sorted(element_list.indexes))

    def __next__(self):
        index = next(self.indexes)
        return self.document.element_list[index]


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
    the or operator | to multiple ElementLists with the singular verion applied, for
    example `foo.filter_by_tags("bar", "baz")` is the same as
    `foo.filter_by_tag("bar") | foo.filter_by_tag("baz")`.

    Similarly, chaining two filter commands is the same as applying the and & operator,
    for example `foo.filter_by_tag("bar").filter_by_tag("baz")` is the same as
    `foo.filter_by_tag("bar") & foo.filter_by_tag("baz")`. Note that this is not the
    case for methods which do not filter, e.g. `add_element`.

    Note:
        As ElementList is implemented using sets internally, you will not be able to
        have an element in an ElementList multiple times.

    Args:
        document (PDFDocument): A reference to the PDF document
        indexes (set, optional): A set (or frozenset) of element indexes. Default to
            all elements in the document.
    """

    def __init__(
        self,
        document: "PDFDocument",
        indexes: Optional[Union[Set[int], FrozenSet[int]]] = None,
    ):
        self.document = document
        if indexes is not None:
            self.indexes = frozenset(indexes)
        else:
            self.indexes = frozenset(range(0, len(document.element_list)))

    def filter_by_tag(self, tag: str) -> "ElementList":
        """
        Returns an `ElementList` containing only those elements containing the given
        tag.
        """
        new_indexes: Set[int] = set()
        for element in self:
            if tag in element.tags:
                new_indexes.add(element.index)
        return self.__add_indexes(new_indexes)

    def filter_by_tags(self, *tags: str) -> "ElementList":
        """
        Returns an `ElementList` containing only those elements containing any of the
        given tags.
        """
        new_indexes: Set[int] = set()
        for element in self:
            if any([tag in element.tags for tag in tags]):
                new_indexes.add(element.index)
        return self.__add_indexes(new_indexes)

    def exclude_ignored(self) -> "ElementList":
        """
        Returns an `ElementList` with all of the ignored elements removed.
        """
        new_indexes: Set[int] = set()
        for element in self:
            if not element.ignore:
                new_indexes.add(element.index)
        return self.__add_indexes(new_indexes)

    def filter_by_page(self, page_number: int) -> "ElementList":
        """
        Returns an `ElementList` containing only those elements on the given page.
        """
        page = self.document.get_page(page_number)
        new_indexes = set(range(page.start_element.index, page.end_element.index + 1))
        return self.__add_indexes(new_indexes)

    def filter_by_pages(self, *page_numbers: int) -> "ElementList":
        """
        Returns an `ElementList` containing only those elements on any of the given
        pages.
        """
        new_indexes: Set[int] = set()
        for page_number in page_numbers:
            page = self.document.get_page(page_number)
            new_indexes |= set(
                range(page.start_element.index, page.end_element.index + 1)
            )
        return self.__add_indexes(new_indexes)

    def filter_by_section_name(self, section_name: str) -> "ElementList":
        """
        Returns an `ElementList` of elements contained in any section with the given
        name. See the documentation for a `Section` for more information.
        """
        new_indexes: Set[int] = set()
        for section in self.document.sectioning.sections:
            if section.name == section_name:
                new_indexes |= set(
                    range(section.start_element.index, section.end_element.index + 1)
                )
        return self.__add_indexes(new_indexes)

    def filter_by_section_names(self, *section_names: str) -> "ElementList":
        """
        Returns an `ElementList` of elements contained in any section with any of the
        given section names. See the documentation for a `Section` for more information.
        """
        new_indexes: Set[int] = set()
        for section in self.document.sectioning.sections:
            if any([section.name == section_name for section_name in section_names]):
                new_indexes |= set(
                    range(section.start_element.index, section.end_element.index + 1)
                )
        return self.__add_indexes(new_indexes)

    def filter_by_section(self, section_str: str) -> "ElementList":
        """
        Returns an `ElementList` of elements contained the given section. Note you need
        to specifcy an exact section, not just the name (i.e. "foo_0" not just "foo").
        See the documentation for a `Section` for more information.
        """
        section = self.document.sectioning.sections_dict[section_str]
        new_indexes: Set[int] = set(
            range(section.start_element.index, section.end_element.index + 1)
        )
        return self.__add_indexes(new_indexes)

    def filter_by_sections(self, *section_strs: str) -> "ElementList":
        """
        Returns an `ElementList` of elements contained any of the given sections. Note
        you need to specifcy an exact section, not just the name (i.e. "foo_0" not just
        "foo"). See the documentation for a `Section` for more information.
        """
        new_indexes: Set[int] = set()
        for section_str in section_strs:
            section = self.document.sectioning.sections_dict[section_str]
            new_indexes |= set(
                range(section.start_element.index, section.end_element.index + 1)
            )
        return self.__add_indexes(new_indexes)

    def to_the_right_of(
        self, element: "PDFElement", inclusive: bool = False
    ) -> "ElementList":
        """
        Returns an `ElementList` of all elements which are to the right of the given
        element.

        If you draw a box from the right hand edge of the element to the right hand
        side of the page, all elements which are partially within this box are returned.

        Note:
            By "to the right of" we really mean "directly to the right of", i.e. the
            returned elements all have at least some part which is vertically alligned
            with the specified element.

        Note:
            Technically the element you specify will satisfy the condition, but we
            assume you do not want that element returned. If you do, you can pass
            `inclusive=True`.

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        bounding_box = BoundingBox(
            element.bounding_box.x1,
            page.width,
            element.bounding_box.y0,
            element.bounding_box.y1,
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if not inclusive:
            results = results.remove_element(element)
        return results

    def to_the_left_of(
        self, element: "PDFElement", inclusive: bool = False
    ) -> "ElementList":
        """
        Returns an `ElementList` of all elements which are to the left of the given
        element.

        If you draw a box from the left hand edge of the element to the left hand
        side of the page, all elements which are partially within this box are returned.

        Note:
            By "to the left of" we really mean "directly to the left of", i.e. the
            returned elements all have at least some part which is vertically alligned
            with the specified element.

        Note:
            Technically the element you specify will satisfy the condition, but we
            assume you do not want that element returned. If you do, you can pass
            `inclusive=True`.

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.
        """
        page_number = element.page_number
        bounding_box = BoundingBox(
            0, element.bounding_box.x1, element.bounding_box.y0, element.bounding_box.y1
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if not inclusive:
            results = results.remove_element(element)
        return results

    def below(
        self, element: "PDFElement", inclusive: bool = False, all_pages: bool = False
    ) -> "ElementList":
        """
        Returns an `ElementList` of all elements which are below the given element.

        If you draw a box from the bottom edge of the element to the bottom of the page,
        all elements which are partially within this box are returned. By default, only
        elements on the same page as the given element are included, but you can pass
        `inclusive=True` to also include the pages which come after (and so are below)
        the page containing the given element.

        Note:
            By "below" we really mean "directly below", i.e. the returned elements all
            have at least some part which is horizontally alligned with the specified
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
        """
        page_number = element.page_number
        bounding_box = BoundingBox(
            element.bounding_box.x0, element.bounding_box.x1, 0, element.bounding_box.y0
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if all_pages:
            for page in self.document.pages:
                if page.page_number <= page_number:
                    continue
                # We're on a page which is located below our element, so the bounding
                # box should be the length of the entire page.
                bounding_box = BoundingBox(
                    element.bounding_box.x0, element.bounding_box.x1, 0, page.height
                )
                results = results | self.filter_partially_within_bounding_box(
                    bounding_box, page.page_number
                )
        if not inclusive:
            results = results.remove_element(element)
        return results

    def above(
        self, element: "PDFElement", inclusive: bool = False, all_pages: bool = False
    ) -> "ElementList":
        """
        Returns an `ElementList` of all elements which are above the given element.

        If you draw a box from the bottom edge of the element to the bottom of the page,
        all elements which are partially within this box are returned. By default, only
        elements on the same page as the given element are included, but you can pass
        `inclusive=True` to also include the pages which come before (and so are above)
        the page containing the given element.

        Note:
            By "above" we really mean "directly above", i.e. the returned elements all
            have at least some part which is horizontally alligned with the specified
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
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        bounding_box = BoundingBox(
            element.bounding_box.x0,
            element.bounding_box.x1,
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
                    element.bounding_box.x0, element.bounding_box.x1, 0, page.height
                )
                results = results | self.filter_partially_within_bounding_box(
                    bounding_box, page.page_number
                )
        if not inclusive:
            results = results.remove_element(element)
        return results

    def vertically_in_line_with(
        self, element: "PDFElement", inclusive: bool = False, all_pages: bool = False
    ) -> "ElementList":
        """
        Returns an `ElementList` of all elements which are vertically in line with the
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
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        bounding_box = BoundingBox(
            element.bounding_box.x0, element.bounding_box.x1, 0, page.height
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if all_pages:
            for page in self.document.pages:
                if page.page_number == page_number:
                    # Already handled page containing element
                    continue
                bounding_box = BoundingBox(
                    element.bounding_box.x0, element.bounding_box.x1, 0, page.height
                )
                results = results | self.filter_partially_within_bounding_box(
                    bounding_box, page.page_number
                )

        if not inclusive:
            results = results.remove_element(element)
        return results

    def horizontally_in_line_with(
        self, element: "PDFElement", inclusive: bool = False
    ) -> "ElementList":
        """
        Returns an `ElementList` of all elements which are horizontally in line with the
        given element.

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
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        bounding_box = BoundingBox(
            0, page.width, element.bounding_box.y0, element.bounding_box.y1
        )
        results = self.filter_partially_within_bounding_box(bounding_box, page_number)
        if not inclusive:
            results = results.remove_element(element)
        return results

    def filter_partially_within_bounding_box(
        self, bounding_box: BoundingBox, page_number: int
    ) -> "ElementList":
        """
        Returns an ElementList of all elements on the given page which are partially
        within the given bounding box.
        """
        new_indexes: Set[int] = set()
        for elem in self.filter_by_page(page_number):
            if elem.partially_within(bounding_box):
                new_indexes.add(elem.index)
        return self.__add_indexes(new_indexes)

    def before(self, element: "PDFElement", inclusive: bool = False) -> "ElementList":
        """
        Returns an ElementList of all elements before the specified element.

        By before, we mean preceeding elements according to their index. The PDFDocument
        will order elements left to right, top to bottom (as you would normally read).

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.
        """
        new_indexes = set([index for index in self.indexes if index < element.index])
        if inclusive:
            new_indexes.add(element.index)
        return self.__add_indexes(new_indexes)

    def after(self, element: "PDFElement", inclusive: bool = False) -> "ElementList":
        """
        Returns an ElementList of all elements after the specified element.

        By after, we mean preceeding elements according to their index. The PDFDocument
        will order elements left to right, top to bottom (as you would normally read).

        Args:
            element (PDFElement): The element in question.
            inclusive (bool, optional): Whether the include `element` in the returned
                results. Default: False.
        """
        new_indexes = set([index for index in self.indexes if index > element.index])
        if inclusive:
            new_indexes.add(element.index)
        return self.__add_indexes(new_indexes)

    def between(
        self,
        start_element: "PDFElement",
        end_element: "PDFElement",
        inclusive: bool = False,
    ):
        """
        Returns an ElementList of all elements between the start and end elements.

        This is done according to the element indexes. The PDFDocument will order
        elements left to right, top to bottom (as you would normally read).

        This is the same as applying `before` with `start_element` and `afeter

        Args:
            start_element (PDFElement): Returned elements will be after this element.
            end_element (PDFElement): Returned elements will be before this element.
            inclusive (bool, optional): Whether the include `start_element` and
                `end_element` in the returned results. Default: False.
        """
        return self.before(end_element, inclusive=inclusive) & self.after(
            start_element, inclusive=inclusive
        )

    def extract_single_element(self) -> "PDFElement":
        """
        Returns only element in the ElementList, provided there is only one element.

        This is mainly for convienence, when you think you've filtered down to a single
        element and you would like to extract said element.

        Raises:
            NoElementFoundError: If there are no elements in the ElementList
            MultipleElementsFoundError: If there is more than one element in the
                ElementList
        """
        if len(self.indexes) == 0:
            raise NoElementFoundError("There are no elements in the ElementList")
        if len(self.indexes) > 1:
            raise MultipleElementsFoundError(
                f"There are {len(self.indexes)} elements in the ElementList"
            )

        return self.document.element_list[list(self.indexes)[0]]

    def add_element(self, element: "PDFElement") -> "ElementList":
        """
        Explicity adds the element to the ElementList.

        Note:
            If the element is already in the ElementList, this does nothing.
        """
        return ElementList(self.document, self.indexes | set([element.index]))

    def add_elements(self, *elements: "PDFElement") -> "ElementList":
        """
        Explicity adds the elements to the ElementList.

        Note:
            If the elements are already in the ElementList, this does nothing.
        """
        return ElementList(
            self.document, self.indexes | set([element.index for element in elements])
        )

    def remove_element(self, element: "PDFElement") -> "ElementList":
        """
        Explicity removes the element from the ElementList.

        Note:
            If the element is not in the ElementList, this does nothing.
        """
        return ElementList(self.document, self.indexes - set([element.index]))

    def remove_elements(self, *elements: "PDFElement") -> "ElementList":
        """
        Explicity removes the elements from the ElementList.

        Note:
            If the elements are not in the ElementList, this does nothing.
        """
        return ElementList(
            self.document, self.indexes - set([element.index for element in elements])
        )

    def __add_indexes(self, new_indexes: Set[int]):
        return self & ElementList(self.document, new_indexes)

    def __iter__(self) -> ElementIterator:
        """
        Returns an ElementIterator class that allows iterating through elements.

        See the documentation for ElementIterator.
        """
        return ElementIterator(self)

    def __contains__(self, element: "PDFElement") -> bool:
        """
        Returns True if the element is in the ElementList, otherwise False.
        """
        index = element.index
        return index in self.indexes

    def __repr__(self):
        return f"<ElementsList of {len(self.indexes)} elements>"

    def __getitem__(self, index):
        """
        Returns the element in position `index` of the ElementList.

        Elements are ordered by their original positions in the document, which is
        left-to-right, top-to-bottom (the same you you read).
        """
        element_index = sorted(self.indexes)[index]
        return self.document.element_list[element_index]

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
