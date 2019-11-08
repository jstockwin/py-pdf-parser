from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .components import PDFDocument, PDFElement


class Utils:
    def __init__(self, document: "PDFDocument"):
        self.document = document

    def tag_elements_by_font(
        self, elements: List["PDFElement"], config: Dict[str, str]
    ):
        for element in elements:
            new_tag = config.get(element.font)
            if new_tag:
                element.add_tag(new_tag)

    def tag_all_elements_by_font(self, config: Dict[str, str]):
        self.tag_elements_by_font(self.document.elements, config)

    def tag_elements_between(
        self, start_element: "PDFElement", end_element: "PDFElement", tag: str
    ):
        for element in self.document.elements_between(start_element, end_element):
            element.add_tag(tag)
