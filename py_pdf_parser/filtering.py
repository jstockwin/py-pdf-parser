from typing import List, TYPE_CHECKING

from collections import namedtuple

if TYPE_CHECKING:
    from .components import PDFDocument

Bound = namedtuple("Bound", ["lower", "upper"])


class ElementIterator:
    index: int
    document: "PDFDocument"

    def __init__(self, element_list: "ElementList"):
        self.index = 0
        self.document = element_list.document
        element_indexes: List[int] = []
        for bound in element_list.bounds:
            element_indexes += range(bound.lower, bound.upper + 1)
        element_indexes.sort()
        self.indexes = iter(element_indexes)

    def __next__(self):
        index = next(self.indexes)
        return self.document.element_list[index]


class ElementList:
    """
    TODO: If the bounds overlap [0, 10], [5, 15] then when we iterate we'll end up
    getting some elements twice, which is bad. We should have some kind of "fix overlap"
    function which removes this problem.
    """

    bounds: List

    def __init__(self, document, bounds):
        self.document: "PDFDocument" = document
        self.bounds: List[Bound] = bounds

    def filter_by_page(self, page_number: int) -> "ElementList":
        """
        Filters to elements on a specific page.
        """
        page_info = self.document.page_info[page_number]
        new_bounds = [
            Bound(
                lower=self.document.element_index(page_info.start_element),
                upper=self.document.element_index(page_info.end_element),
            )
        ]
        return self.__add_filter(new_bounds)

    def filter_by_pages(self, *page_numbers: int) -> "ElementList":
        """
        Filters to elements on any of the specified pages.
        """
        new_bounds = []
        for page_number in page_numbers:
            page_info = self.document.page_info[page_number]
            new_bounds.append(
                Bound(
                    lower=self.document.element_index(page_info.start_element),
                    upper=self.document.element_index(page_info.end_element),
                )
            )
        return self.__add_filter(new_bounds)

    def filter_by_tag(self, tag: str) -> "ElementList":
        """
        Filters to elements with a specific tag.
        """
        new_bounds = []
        for element in self:
            if tag in element.tags:
                element_index = self.document.element_index(element)
                new_bounds.append(Bound(lower=element_index, upper=element_index))
        return self.__add_filter(new_bounds)

    def filter_by_tags(self, *tags: str) -> "ElementList":
        """
        Filters to elements with any of the specific tags.
        """
        new_bounds = []
        for element in self:
            if any([tag in element.tags for tag in tags]):
                element_index = self.document.element_index(element)
                new_bounds.append(Bound(lower=element_index, upper=element_index))
        return self.__add_filter(new_bounds)

    def exclude_ignored(self) -> "ElementList":
        """
        Removes ignored elements.
        """
        new_bounds = []
        for element in self:
            if not element.ignore:
                element_index = self.document.element_index(element)
                new_bounds.append(Bound(lower=element_index, upper=element_index))
        return self.__add_filter(new_bounds)

    def filter_by_section_name(self, section_name: str) -> "ElementList":
        """
        Filters to elements within any section with the given name.
        """
        new_bounds = []
        for section in self.document.sectioning.sections:
            if section.name == section_name:
                new_bounds.append(
                    Bound(
                        lower=self.document.element_index(section.start_element),
                        upper=self.document.element_index(section.end_element),
                    )
                )
        return self.__add_filter(new_bounds)

    def filter_by_section_names(self, *section_names: str) -> "ElementList":
        """
        Filters to elements within any section with any of the given names.
        """
        new_bounds = []
        for section in self.document.sectioning.sections:
            if section.name in section_names:
                new_bounds.append(
                    Bound(
                        lower=self.document.element_index(section.start_element),
                        upper=self.document.element_index(section.end_element),
                    )
                )
        return self.__add_filter(new_bounds)

    def filter_by_section(self, section_str: str) -> "ElementList":
        """
        Filters to elements within the given section.
        """
        section = self.document.sectioning.sections_dict[section_str]
        new_bounds = [
            Bound(
                lower=self.document.element_index(section.start_element),
                upper=self.document.element_index(section.end_element),
            )
        ]
        return self.__add_filter(new_bounds)

    def filter_by_sections(self, *section_strs: str) -> "ElementList":
        """
        Filters to elements within any of the given sections.
        """
        new_bounds = []
        for section_str in section_strs:
            section = self.document.sectioning.sections_dict[section_str]
            new_bounds.append(
                Bound(
                    lower=self.document.element_index(section.start_element),
                    upper=self.document.element_index(section.end_element),
                )
            )
        return self.__add_filter(new_bounds)

    def __add_filter(self, new_bounds: List[Bound]) -> "ElementList":
        return ElementList(self.document, _combine_bounds(self.bounds, new_bounds))

    def __iter__(self):
        return ElementIterator(self)

    def __repr__(self):
        num_elems = sum([top + 1 - bottom for bottom, top in self.bounds])
        return f"<ElementsList of {num_elems} elements>"


def _combine_bounds(bounds_a: List[Bound], bounds_b: List[Bound]) -> List[Bound]:
    """
    Given two lists of bounds, combines them by applying the logical and to the bounds.

    TODO: This is actually not very efficient when dealing with the element specific
    things, e.g. by tag or excluding ignored elements (however it is efficient for
    pages and sections). We should probably add some documentation to explain that you
    should first use sections and pages as much as possible before filtering by tags.
    Specifically, filter_by_tag(a).filter_by_tag(b) will be n**2.
    """
    bounds = []
    for bound_a in bounds_a:
        for bound_b in bounds_b:
            lower = max(bound_a.lower, bound_b.lower)
            upper = min(bound_a.upper, bound_b.upper)

            if lower <= upper:
                bounds.append(Bound(lower=lower, upper=upper))

    return bounds


def _sanitise_bounds(bounds: List[Bound]):
    """
    Removes overlapping bounds and merges continuous bounds.

    For example:
    [0, 1], [1, 2] -> [0, 2]
    [0, 1], [2, 3] -> [0, 3]
    [0, 4], [1, 2] -> [0, 4]
    [0, 4], [2, 4] -> [0, 4]

    TODO: Again, this is inefficient and I don't love the code...
    """
    old_len = len(bounds)
    new_len = None
    while old_len != new_len:
        old_len = len(bounds)
        used: List[int] = []
        new_bounds = []
        for idx_a, bound_a in enumerate(bounds):
            for idx_b, bound_b in enumerate(bounds):
                if idx_a == idx_b or idx_a in used or idx_b in used:
                    continue

                if bound_a.upper >= bound_b.lower - 1:
                    # Bounds overlap so can be merged
                    new_bound = Bound(
                        lower=min(bound_a.lower, bound_b.lower),
                        upper=max(bound_a.upper, bound_b.upper),
                    )
                    used += [idx_a, idx_b]
                    new_bounds.append(new_bound)
                    break
            else:
                if idx_a not in used:
                    used.append(idx_a)
                    new_bounds.append(bound_a)

        bounds = new_bounds
        new_len = len(bounds)
    return bounds
