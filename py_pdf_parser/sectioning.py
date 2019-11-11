from typing import Dict, TYPE_CHECKING

from collections import defaultdict

if TYPE_CHECKING:
    from .components import PDFDocument, PDFElement


class Section:
    document: "PDFDocument"
    name: str
    unique_name: str
    start_elemet: "PDFElement"
    end_element: "PDFElement"

    def __init__(self, document, name, unique_name, start_elemet, end_element):
        self.document = document
        self.name = name
        self.unique_name = unique_name
        self.start_elemet = start_elemet
        self.end_element = end_element

    def elements(self, include_ignored=True):
        return self.document.elements_between(
            self.start_elemet, self.end_element, include_ignored
        )


class Sectioning:
    document: "PDFDocument"
    name_counts: Dict[str, int] = defaultdict(int)
    __sections: Dict[str, Section] = {}

    def __init__(self, document: "PDFDocument"):
        self.document = document

    def create_section(
        self, name: str, start_element: "PDFElement", end_element: "PDFElement"
    ):
        current_count = self.name_counts[name]
        unique_name = f"{name}_{current_count}"
        self.name_counts[name] += 1

        section = Section(self.document, name, unique_name, start_element, end_element)
        self.__sections[unique_name] = section
        return section

    @property
    def sections(self):
        return self.__sections.values()
