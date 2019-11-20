from typing import (
    Union,
    Set,
    FrozenSet,
    Optional,
    Iterable,
    Iterator,
    Type,
    TYPE_CHECKING,
)

from .common import BoundingBox
from .exceptions import NoElementFoundError, MultipleElementsFoundError

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
        return self.document.element_list[index]


class ElementList(Iterable):
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
        new_indexes: Set[int] = set()
        for element in self:
            if tag in element.tags:
                new_indexes.add(element.index)
        return self.__add_indexes(new_indexes)

    def filter_by_tags(self, *tags: str) -> "ElementList":
        new_indexes: Set[int] = set()
        for element in self:
            if any([tag in element.tags for tag in tags]):
                new_indexes.add(element.index)
        return self.__add_indexes(new_indexes)

    def exclude_ignored(self) -> "ElementList":
        new_indexes: Set[int] = set()
        for element in self:
            if not element.ignore:
                new_indexes.add(element.index)
        return self.__add_indexes(new_indexes)

    def filter_by_page(self, page_number: int) -> "ElementList":
        page = self.document.get_page(page_number)
        new_indexes = set(range(page.start_element.index, page.end_element.index + 1))
        return self.__add_indexes(new_indexes)

    def filter_by_pages(self, *page_numbers: int) -> "ElementList":
        new_indexes: Set[int] = set()
        for page_number in page_numbers:
            page = self.document.get_page(page_number)
            new_indexes |= set(
                range(page.start_element.index, page.end_element.index + 1)
            )
        return self.__add_indexes(new_indexes)

    def filter_by_section_name(self, section_name: str) -> "ElementList":
        new_indexes: Set[int] = set()
        for section in self.document.sectioning.sections:
            if section.name == section_name:
                new_indexes |= set(
                    range(section.start_element.index, section.end_element.index + 1)
                )
        return self.__add_indexes(new_indexes)

    def filter_by_section_names(self, *section_names: str) -> "ElementList":
        new_indexes: Set[int] = set()
        for section in self.document.sectioning.sections:
            if any([section.name == section_name for section_name in section_names]):
                new_indexes |= set(
                    range(section.start_element.index, section.end_element.index + 1)
                )
        return self.__add_indexes(new_indexes)

    def filter_by_section(self, section_str: str) -> "ElementList":
        section = self.document.sectioning.sections_dict[section_str]
        new_indexes: Set[int] = set(
            range(section.start_element.index, section.end_element.index + 1)
        )
        return self.__add_indexes(new_indexes)

    def filter_by_sections(self, *section_strs: str) -> "ElementList":
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
        page_number = element.page_number
        page = self.document.get_page(page_number)
        bounding_box = BoundingBox(
            element.bounding_box.x1,
            page.width,
            element.bounding_box.y0,
            element.bounding_box.y1,
        )
        new_indexes: Set[int] = set()
        if inclusive:
            new_indexes.add(element.index)
        for elem in self:
            if elem != element and elem.partially_within(bounding_box):
                new_indexes.add(elem.index)
        return self.__add_indexes(new_indexes) & self.filter_by_page(page_number)

    def to_the_left_of(
        self, element: "PDFElement", inclusive: bool = False
    ) -> "ElementList":
        page_number = element.page_number
        bounding_box = BoundingBox(
            0, element.bounding_box.x1, element.bounding_box.y0, element.bounding_box.y1
        )
        new_indexes: Set[int] = set()
        if inclusive:
            new_indexes.add(element.index)
        for elem in self:
            if elem != element and elem.partially_within(bounding_box):
                new_indexes.add(elem.index)
        return self.__add_indexes(new_indexes) & self.filter_by_page(page_number)

    def below(self, element: "PDFElement", inclusive: bool = False) -> "ElementList":
        """
        Returns all the elements that are underneath the given element.

        Will return an ElementList of all PDFElements which are partially within the
        box created by extending the given PDFElement to the bottom of the page.

        TODO: We should extend this to allow it to work on all proceeding pages.
        TODO: It needs to be made clear that won't return all elements below the
        bottom of this element - they still need to be in line.
        """
        page_number = element.page_number
        bounding_box = BoundingBox(
            element.bounding_box.x0, element.bounding_box.x1, 0, element.bounding_box.y0
        )
        new_indexes: Set[int] = set()
        if inclusive:
            new_indexes.add(element.index)
        for elem in self:
            if elem != element and elem.partially_within(bounding_box):
                new_indexes.add(elem.index)
        return self.__add_indexes(new_indexes) & self.filter_by_page(page_number)

    def above(self, element: "PDFElement", inclusive: bool = False) -> "ElementList":
        """
        Returns all the elements that are above the given element.

        Will return an ElementList of all PDFElements which are partially within the
        box created by extending the given PDFElement to the top of the page.

        TODO: We should extend this to allow it to work on all preceeding pages.
        TODO: It needs to be made clear that won't return all elements above the
        top of this element - they still need to be in line.
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        bounding_box = BoundingBox(
            element.bounding_box.x0,
            element.bounding_box.x1,
            element.bounding_box.y1,
            page.height,
        )
        new_indexes: Set[int] = set()
        if inclusive:
            new_indexes.add(element.index)
        for elem in self:
            if elem != element and elem.partially_within(bounding_box):
                new_indexes.add(elem.index)
        return self.__add_indexes(new_indexes) & self.filter_by_page(page_number)

    def vertically_in_line_with(
        self, element: "PDFElement", inclusive: bool = False
    ) -> "ElementList":
        """
        TODO: Refactor inclusive above to match this
        TODO: Should there be an __method(bbox) to handle the latter part of this?
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        bounding_box = BoundingBox(
            element.bounding_box.x0, element.bounding_box.x1, 0, page.height
        )
        new_indexes: Set[int] = set()
        if inclusive:
            new_indexes.add(element.index)
        for elem in self:
            if elem == element and not inclusive:
                continue
            if elem.partially_within(bounding_box):
                new_indexes.add(elem.index)
        return self.__add_indexes(new_indexes) & self.filter_by_page(page_number)

    def horizontally_in_line_with(
        self, element: "PDFElement", inclusive: bool = False
    ) -> "ElementList":
        """
        TODO: Refactor inclusive above to match this
        TODO: Should there be an __method(bbox) to handle the latter part of this?
        """
        page_number = element.page_number
        page = self.document.get_page(page_number)
        bounding_box = BoundingBox(
            0, page.width, element.bounding_box.y0, element.bounding_box.y1
        )
        new_indexes: Set[int] = set()
        if inclusive:
            new_indexes.add(element.index)
        for elem in self:
            if elem == element and not inclusive:
                continue
            if elem.partially_within(bounding_box):
                new_indexes.add(elem.index)
        return self.__add_indexes(new_indexes) & self.filter_by_page(page_number)

    def before(self, element: "PDFElement", inclusive: bool = False) -> "ElementList":
        new_indexes = set([index for index in self.indexes if index < element.index])
        if inclusive:
            new_indexes.add(element.index)
        return self.__add_indexes(new_indexes)

    def after(self, element: "PDFElement", inclusive: bool = False) -> "ElementList":
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
        return self.before(end_element, inclusive=inclusive) & self.after(
            start_element, inclusive=inclusive
        )

    def extract_single_element(self) -> "PDFElement":
        if len(self.indexes) == 0:
            raise NoElementFoundError("There are no elements in the ElementList")
        if len(self.indexes) > 1:
            raise MultipleElementsFoundError(
                f"There are {len(self.indexes)} elements in the ElementList"
            )

        return self.document.element_list[list(self.indexes)[0]]

    def __add_indexes(self, new_indexes: Set[int]):
        return self & ElementList(self.document, new_indexes)

    def __iter__(self) -> ElementIterator:
        return ElementIterator(self)

    def __contains__(self, element: "PDFElement") -> bool:
        index = element.index
        return index in self.indexes

    def __repr__(self):
        return f"<ElementsList of {len(self.indexes)} elements>"

    def __getitem__(self, index):
        element_index = sorted(self.indexes)[index]
        return self.document.element_list[element_index]

    def __eq__(self, other: object) -> bool:
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
        return len(self.indexes)

    def __sub__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes - other.indexes)

    def __or__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes | other.indexes)

    def __xor__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes ^ other.indexes)

    def __and__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes & other.indexes)
