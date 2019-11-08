from typing import Dict, List

from .components import PDFElement, PDFDocument


def tag_elements_by_font(elements: List[PDFElement], config: Dict[str, str]):
    for element in elements:
        new_tag = config.get(element.font)
        if new_tag:
            element.add_tag(new_tag)


def tag_all_elements_by_font(document: PDFDocument, config: Dict[str, str]):
    tag_elements_by_font(document.elements, config)
