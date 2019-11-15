from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .components import PDFDocument
    from .filtering import ElementList


class Utils:
    def __init__(self, document: "PDFDocument"):
        self.document = document

    def tag_elements_by_font(self, elements: "ElementList", config: Dict[str, str]):
        for element in elements:
            new_tag = config.get(element.font)
            if new_tag:
                element.add_tag(new_tag)

    def tag_all_elements_by_font(self, config: Dict[str, str]):
        self.tag_elements_by_font(self.document.elements, config)
