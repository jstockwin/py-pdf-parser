from typing import Set, Optional, TYPE_CHECKING

from .common import BoundingBox

if TYPE_CHECKING:
    from .components import PDFDocument, PDFElement


class ElementIterator:
    index: int
    document: "PDFDocument"

    def __init__(self, element_list: "ElementList"):
        self.index = 0
        self.document = element_list.document
        self.indexes = iter(sorted(element_list.indexes))

    def __next__(self):
        index = next(self.indexes)
        return self.document.element_list[index]


class ElementList:
    def __init__(self, document: "PDFDocument", indexes: Optional[Set[int]] = None):
        self.document = document
        if indexes is not None:
            self.indexes = indexes
        else:
            self.indexes = set(range(0, len(document.element_list)))

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
        page_info = self.document.page_info[page_number]
        new_indexes = set(
            range(page_info.start_element.index, page_info.end_element.index + 1)
        )
        return self.__add_indexes(new_indexes)

    def filter_by_pages(self, *page_numbers: int) -> "ElementList":
        new_indexes: Set[int] = set()
        for page_number in page_numbers:
            page_info = self.document.page_info[page_number]
            new_indexes |= set(
                range(page_info.start_element.index, page_info.end_element.index + 1)
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

    def to_the_right_of(self, element: "PDFElement") -> "ElementList":
        page_number = self.document.element_page(element)
        page_info = self.document.page_info[page_number]
        bounding_box = BoundingBox(
            element.bounding_box.x1 - 1,
            page_info.width + 1,
            element.bounding_box.y0 - 1,
            element.bounding_box.y1 + 1,
        )
        new_indexes: Set[int] = set()
        for element in self:
            if element.partially_within(bounding_box):
                new_indexes.add(element.index)
        return self.__add_indexes(new_indexes) & self.filter_by_page(page_number)

    def after(self, element: "PDFElement") -> "ElementList":
        new_indexes = set([index for index in self.indexes if index > element.index])
        return self.__add_indexes(new_indexes)

    def extract_single_element(self) -> "PDFElement":
        if not len(self.indexes) != 1:
            raise Exception(
                f"To extract a single element there must be exactly one element in "
                "your ElementList. You have {len(self.indexes)}"
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

    def __sub__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes - other.indexes)

    def __or__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes | other.indexes)

    def __xor__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes ^ other.indexes)

    def __and__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes & other.indexes)
