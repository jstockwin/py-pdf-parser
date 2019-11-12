from typing import Set, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .components import PDFDocument


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
                new_indexes.add(self.document.element_index(element))
        return self.__add_indexes(new_indexes)

    def filter_by_tags(self, *tags: str) -> "ElementList":
        new_indexes: Set[int] = set()
        for element in self:
            if any([tag in element.tags for tag in tags]):
                new_indexes.add(self.document.element_index(element))
        return self.__add_indexes(new_indexes)

    def exclude_ignored(self) -> "ElementList":
        new_indexes: Set[int] = set()
        for element in self:
            if not element.ignore:
                new_indexes.add(self.document.element_index(element))
        return self.__add_indexes(new_indexes)

    def filter_by_page(self, page_number: int) -> "ElementList":
        page_info = self.document.page_info[page_number]
        new_indexes = set(
            range(
                self.document.element_index(page_info.start_element),
                self.document.element_index(page_info.end_element),
            )
        )
        return self.__add_indexes(new_indexes)

    def filter_by_pages(self, *page_numbers: int) -> "ElementList":
        new_indexes: Set[int] = set()
        for page_number in page_numbers:
            page_info = self.document.page_info[page_number]
            new_indexes |= set(
                range(
                    self.document.element_index(page_info.start_element),
                    self.document.element_index(page_info.end_element),
                )
            )
        return self.__add_indexes(new_indexes)

    def filter_by_section_name(self, section_name: str) -> "ElementList":
        new_indexes: Set[int] = set()
        for section in self.document.sectioning.sections:
            if section.name == section_name:
                new_indexes |= set(
                    range(
                        self.document.element_index(section.start_element),
                        self.document.element_index(section.end_element),
                    )
                )
        return self.__add_indexes(new_indexes)

    def filter_by_section_names(self, *section_names: str) -> "ElementList":
        new_indexes: Set[int] = set()
        for section in self.document.sectioning.sections:
            if any([section.name == section_name for section_name in section_names]):
                new_indexes |= set(
                    range(
                        self.document.element_index(section.start_element),
                        self.document.element_index(section.end_element),
                    )
                )
        return self.__add_indexes(new_indexes)

    def filter_by_section(self, section_str: str) -> "ElementList":
        section = self.document.sectioning.sections_dict[section_str]
        new_indexes: Set[int] = set(
            range(
                self.document.element_index(section.start_element),
                self.document.element_index(section.end_element),
            )
        )
        return self.__add_indexes(new_indexes)

    def filter_by_sections(self, *section_strs: str) -> "ElementList":
        new_indexes: Set[int] = set()
        for section_str in section_strs:
            section = self.document.sectioning.sections_dict[section_str]
            new_indexes |= set(
                range(
                    self.document.element_index(section.start_element),
                    self.document.element_index(section.end_element),
                )
            )
        return self.__add_indexes(new_indexes)

    def __add_indexes(self, new_indexes: Set[int]):
        return self & ElementList(self.document, new_indexes)

    def __iter__(self) -> ElementIterator:
        return ElementIterator(self)

    def __repr__(self):
        return f"<ElementsList of {len(self.indexes)} elements>"

    def __sub__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes - other.indexes)

    def __or__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes | other.indexes)

    def __xor__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes ^ other.indexes)

    def __and__(self, other: "ElementList") -> "ElementList":
        return ElementList(self.document, self.indexes & other.indexes)
