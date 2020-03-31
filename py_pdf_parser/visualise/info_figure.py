from typing import Dict, List, Optional, TYPE_CHECKING

from matplotlib.backend_bases import MouseButton

if TYPE_CHECKING:
    from py_pdf_parser.components import PDFElement


def get_clicked_element_info(clicked_elements: Dict[MouseButton, "PDFElement"]) -> str:
    left_element = clicked_elements.get(MouseButton.LEFT)
    right_element = clicked_elements.get(MouseButton.RIGHT)

    output = []

    output.append("Left clicked element:")
    output.append("---------------------")
    output += _get_element_info(left_element)
    output.append("")

    output.append("Right clicked element:")
    output.append("---------------------")
    output += _get_element_info(right_element)
    output.append("")

    output.append("Element comparison:")
    output.append("-------------------")
    output += _get_element_comparison_info(left_element, right_element)
    return "\n".join(output)


def _get_element_info(element: Optional["PDFElement"]) -> List[str]:
    if not element:
        return ["Click an element to see details"]
    return [
        f"Text: {element.text(stripped=False)}",
        f"Font: {element.font}",
        f"Tags: {element.tags}",
        f"Bounding box: {element.bounding_box}",
        f"Width: {element.bounding_box.width}",
        f"Height: {element.bounding_box.height}",
    ]


def _get_element_comparison_info(
    element1: Optional["PDFElement"], element2: Optional["PDFElement"]
) -> List[str]:
    if element1 is None or element2 is None:
        return ["Left click one element and right click another to see comparison"]

    bbox1 = element1.bounding_box
    bbox2 = element2.bounding_box

    # Height
    height_diff = abs(bbox1.height - bbox2.height)
    relative_height_diff = height_diff / bbox1.height

    # Line margin (i.e. vertical gap)
    line_margin = max(bbox1.y0 - bbox2.y1, bbox2.y0 - bbox1.y1)
    relative_line_margin = line_margin / bbox1.height

    # Alignment
    alignments = {
        "left": abs(bbox1.x0 - bbox2.x0),
        "right": abs(bbox1.x1 - bbox2.x1),
        "center": abs((bbox1.x0 + bbox1.x1) / 2 - (bbox2.x0 + bbox2.x1) / 2),
    }
    sorted_alignments = sorted(alignments.items(), key=lambda x: x[1])
    alignment_name, alignment_value = sorted_alignments[0]
    relative_alignment_value = alignment_value / bbox1.height

    return [
        "Note 'relative' is relative to the left clicked element",
        f"Height diff: {height_diff}",
        f"Relative height diff {relative_height_diff}",
        f"Line margin: {line_margin}",
        f"Relative line margin: {relative_line_margin}",
        f"Closest alignment: {alignment_value} ({alignment_name})",
        f"Relative alignment: {relative_alignment_value}",
    ]
