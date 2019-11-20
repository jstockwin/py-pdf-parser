from typing import TYPE_CHECKING, Any, List, Dict, Optional

from itertools import chain

from .exceptions import (
    TableExtractionError,
    NoElementFoundError,
    InvalidTableError,
    InvalidTableHeaderError,
)

if TYPE_CHECKING:
    from .filtering import ElementList
    from .components import PDFElement


def extract_simple_table(elements: "ElementList") -> List[List[Optional["PDFElement"]]]:
    """
    Returns elements structured as a table.
    """
    first_row = elements.to_the_right_of(elements[0], inclusive=True)
    first_column = elements.below(elements[0], inclusive=True)

    table: List[List[Optional["PDFElement"]]] = []
    for left_hand_element in first_column:
        row: List[Optional["PDFElement"]] = []
        for top_element in first_row:
            element = elements.to_the_right_of(left_hand_element, inclusive=True).below(
                top_element, inclusive=True
            )
            try:
                row.append(element.extract_single_element())
            except NoElementFoundError:
                row.append(None)
        table.append(row)

    table_size = sum(len(row) for row in table)
    if table_size != len(elements):
        raise TableExtractionError(
            f"Number of elements in table ({table_size}) does not match number of "
            f"elements passed {len(elements)}. Perhaps try extract_table instead of "
            "extract_simple_table."
        )

    __validate_table_shape(table)
    return table


def extract_table(elements: "ElementList") -> List[List[Optional["PDFElement"]]]:
    table = []
    rows = set()
    cols = set()
    for element in elements:
        row = elements.horizontally_in_line_with(element, inclusive=True)
        rows.add(row)
        col = elements.vertically_in_line_with(element, inclusive=True)
        cols.add(col)

    # Check no element is in multiple rows or columns
    if sum([len(row) for row in rows]) != len(set(chain.from_iterable(rows))):
        raise TableExtractionError("An element is in multiple rows")
    if sum([len(col) for col in cols]) != len(set(chain.from_iterable(cols))):
        raise TableExtractionError("An element is in multiple columns")

    sorted_rows = sorted(
        rows, key=lambda row: min([elem.bounding_box.y0 for elem in row]), reverse=True
    )
    sorted_cols = sorted(
        cols, key=lambda col: min([elem.bounding_box.x0 for elem in col])
    )

    for row in sorted_rows:
        table_row = []
        for col in sorted_cols:
            try:
                element = (row & col).extract_single_element()
            except NoElementFoundError:
                element = None
            table_row.append(element)
        table.append(table_row)

    __validate_table_shape(table)
    return table


def extract_text_from_simple_table(elements: "ElementList") -> List[List[str]]:
    return __extract_text_from_table(extract_simple_table(elements))


def extract_text_from_table(elements: "ElementList") -> List[List[str]]:
    return __extract_text_from_table(extract_table(elements))


def add_header_to_table(
    table: List[List[str]], header: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    __validate_table_shape(table)
    header_provided = bool(header)
    if header is None:
        header = table[0]
    elif len(header) != len(table[0]):
        raise InvalidTableHeaderError(
            f"Header length of {len(header)} does not match the width of the table "
            f"({len(table[0])})"
        )
    new_table = []
    for row in table:
        new_row = {header[idx]: element for idx, element in enumerate(row)}
        new_table.append(new_row)

    if not header_provided:
        # The first row was the header, and we still mapped it. Remove it.
        # Note: We don't want to do table.pop(0) at the top as that would modify the
        # object that we were passed.
        new_table.pop(0)
    return new_table


def __extract_text_from_table(
    table: List[List[Optional["PDFElement"]]],
) -> List[List[str]]:
    __validate_table_shape(table)
    new_table = []
    for row in table:
        new_row = [element.text if element is not None else "" for element in row]
        new_table.append(new_row)
    return new_table


def __validate_table_shape(table: List[List[Any]]):
    for idx, row in enumerate(table[1:]):
        if not len(row) == len(table[0]):
            raise InvalidTableError(
                f"Table not rectangular, row 0 has {len(table[0])} elements but row "
                f"{idx + 1} has {len(row)}."
            )
