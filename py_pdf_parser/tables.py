from typing import TYPE_CHECKING, Any, List, Set, Dict, Optional

from itertools import chain

from .exceptions import (
    TableExtractionError,
    NoElementFoundError,
    MultipleElementsFoundError,
    InvalidTableError,
    InvalidTableHeaderError,
)

if TYPE_CHECKING:
    from .filtering import ElementList
    from .components import PDFElement


def extract_simple_table(
    elements: "ElementList",
    as_text: bool = False,
    strip_text: bool = True,
    tolerance: float = 0.0,
) -> List[List]:
    """
    Returns elements structured as a table.

    Given an ElementList, tries to extract a structured table by examining which
    elements are aligned. To use this function, the table must contain no gaps, i.e.
    should be a full N x M table with an element in each cell. There must be a clear
    gap between each row and between each column which contains no elements, and
    a single cell cannot contain multiple elements.

    If your table has empty cells, you can use `extract_table` instead. If you fail
    to satisfy any of the other conditions listed above, that case is not yet supported.

    Args:
        elements (ElementList): A list of elements to extract into a table.
        as_text (bool, optional): Whether to extract the text from each element instead
            of the PDFElement itself. Default: False.
        strip_text (bool, optional): Whether to strip the text for each element of the
                table (Only relevant if as_text is True). Default: True.
        tolerance (int, optional): For elements to be counted as in the same row or
            column, they must overlap by at least `tolerance`. Default: 0.

    Raises:
        TableExtractionError: If something goes wrong.

    Returns:
        list[list]: a list of rows, which are lists of PDFElements or strings
            (depending on the value of as_text).
    """
    first_row = elements.to_the_right_of(
        elements[0], inclusive=True, tolerance=tolerance
    )
    first_column = elements.below(elements[0], inclusive=True, tolerance=tolerance)

    table: List[List] = []
    for left_hand_element in first_column:
        row: List = []
        for top_element in first_row:
            element = elements.to_the_right_of(
                left_hand_element, inclusive=True, tolerance=tolerance
            ).below(top_element, inclusive=True, tolerance=tolerance)
            try:
                row.append(element.extract_single_element())
            except NoElementFoundError as err:
                raise TableExtractionError(
                    "Element not found, there appears to be a gap in the table. "
                    "Please try extract_table() instead."
                ) from err
            except MultipleElementsFoundError as err:
                raise TableExtractionError(
                    "Multiple elements appear to be in the place of one cell in the "
                    "table. Please try extract_table() instead."
                ) from err
        table.append(row)

    table_size = sum(len(row) for row in table)
    if table_size != len(elements):
        raise TableExtractionError(
            f"Number of elements in table ({table_size}) does not match number of "
            f"elements passed {len(elements)}. Perhaps try extract_table instead of "
            "extract_simple_table."
        )

    if as_text:
        return get_text_from_table(table, strip_text=strip_text)

    _validate_table_shape(table)
    return table


def extract_table(
    elements: "ElementList",
    as_text: bool = False,
    strip_text: bool = True,
    fix_element_in_multiple_rows: bool = False,
    fix_element_in_multiple_cols: bool = False,
    tolerance: float = 0.0,
) -> List[List]:
    """
    Returns elements structured as a table.

    Given an ElementList, tries to extract a structured table by examining which
    elements are aligned. There must be a clear gap between each row and between each
    column which contains no elements, and a single cell cannot contain multiple
    elements.

    If you fail to satisfy any of the other conditions listed above, that case is not
    yet supported.

    Args:
        elements (ElementList): A list of elements to extract into a table.
        as_text (bool, optional): Whether to extract the text from each element instead
            of the PDFElement itself. Default: False.
        strip_text (bool, optional): Whether to strip the text for each element of the
            table (Only relevant if as_text is True). Default: True.
        fix_element_in_multiple_rows (bool, optional): If a table element is in line
            with elements in multiple rows, a TableExtractionError will be raised unless
            this argument is set to True. When True, any elements detected in multiple
            rows will be placed into the first row. This is only recommended if you
            expect this to be the case in your table. Default: False.
        fix_element_in_multiple_cols (bool, optional): If a table element is in line
            with elements in multiple cols, a TableExtractionError will be raised unless
            this argument is set to True. When True, any elements detected in multiple
            cols will be placed into the first col. This is only recommended if you
            expect this to be the case in your table. Default: False.
        tolerance (int, optional): For elements to be counted as in the same row or
            column, they must overlap by at least `tolerance`. Default: 0.

    Raises:
        TableExtractionError: If something goes wrong.

    Returns:
        list[list]: a list of rows, which are lists of PDFElements or strings
            (depending on the value of as_text).
    """
    table = []
    rows = set()
    cols = set()
    for element in elements:
        row = elements.horizontally_in_line_with(
            element, inclusive=True, tolerance=tolerance
        )
        rows.add(row)
        col = elements.vertically_in_line_with(
            element, inclusive=True, all_pages=True, tolerance=tolerance
        )
        cols.add(col)

    # Check no element is in multiple rows or columns
    if fix_element_in_multiple_rows:
        _fix_rows(rows, elements)
    if fix_element_in_multiple_cols:
        _fix_cols(cols, elements)
    if sum([len(row) for row in rows]) != len(set(chain.from_iterable(rows))):
        raise TableExtractionError("An element is in multiple rows")
    if sum([len(col) for col in cols]) != len(set(chain.from_iterable(cols))):
        raise TableExtractionError("An element is in multiple columns")

    sorted_rows = sorted(
        rows,
        key=lambda row: (
            row[0].page_number,
            max(-(elem.bounding_box.y1) for elem in row),
        ),
    )
    sorted_cols = sorted(
        cols, key=lambda col: max(elem.bounding_box.x0 for elem in col)
    )

    for row in sorted_rows:
        table_row = []
        for col in sorted_cols:
            try:
                element = (row & col).extract_single_element()
            except NoElementFoundError:
                element = None
            except MultipleElementsFoundError as err:
                raise TableExtractionError(
                    "Multiple elements appear to be in the place of one cell in the "
                    "table. It could be worth trying to add a tolerance."
                ) from err
            table_row.append(element)
        table.append(table_row)

    if as_text:
        return get_text_from_table(table, strip_text=strip_text)

    _validate_table_shape(table)
    return table


def add_header_to_table(
    table: List[List[str]], header: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    """
    Given a table (list of lists) of strings, returns a list of dicts mapping the
    table header to the values.

    Given a table, a list of rows which are lists of strings, returns a new table
    which is a list of rows which are dictionaries mapping the header values to the
    table values.

    Args:
        table: The table (a list of lists of strings).
        header (list, optional): The header to use. If not provided, the first row of
            the table will be used instead. Your header must be the same width as your
            table, and cannot contain the same entry multiple times.

    Raises:
        InvalidTableHeaderError: If the width of the header does not match the width of
            the table, or if the header contains duplicate entries.

    Returns:
        list[dict]: A list of dictionaries, where each entry in the list is a row in the
        table, and a row in the table is represented as a dictionary mapping the header
        to the values.
    """
    _validate_table_shape(table)
    header_provided = bool(header)
    if header is None:
        if len(table) == 0:
            raise InvalidTableError("Cannot extract header from empty table")
        header = table[0]
    elif len(table) == 0:
        return []
    elif len(header) != len(table[0]):
        raise InvalidTableHeaderError(
            f"Header length of {len(header)} does not match the width of the table "
            f"({len(table[0])})"
        )
    elif len(header) != len(set(header)):
        raise InvalidTableHeaderError("Header contains repeated elements")
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


def get_text_from_table(
    table: List[List[Optional["PDFElement"]]], strip_text: bool = True
) -> List[List[str]]:
    """
    Given a table (of PDFElements or None), returns a table (of element.text() or '').

    Args:
        table: The table (a list of lists of PDFElements).
        strip_text (bool, optional): Whether to strip the text for each element of the
                table. Default: True.

    Returns:
        list[list[str]]: a list of rows, which are lists of strings.
    """
    _validate_table_shape(table)
    new_table = []
    for row in table:
        new_row = [
            element.text(strip_text) if element is not None else "" for element in row
        ]
        new_table.append(new_row)
    return new_table


def _validate_table_shape(table: List[List[Any]]):
    """
    Checks that all rows (and therefore all columns) are the same length.
    """
    if len(table) < 1:
        return
    first_row_len = len(table[0])
    for idx, row in enumerate(table[1:]):
        if not len(row) == first_row_len:
            raise InvalidTableError(
                f"Table not rectangular, row 0 has {first_row_len} elements but row "
                f"{idx + 1} has {len(row)}."
            )


def _fix_rows(rows: Set["ElementList"], elements: "ElementList") -> None:
    """
    Sometimes an element may span over multiple rows. For example:
    ---------
    | A | B |
    ----|   |
    | C |   |
    ---------
    In this, case, when extract_table scans for element in line with A it will pick up
    A and B. When it scans B it will get A, B and C, and when it scans C it will get B
    and C. This results in three distinct rows, AB, ABC, BC. This function will fix
    this by putting any merged cells into the top row, resulting in one row AB and the
    other with just C.

    To do this, we check which element is in multiple rows, get which rows it is in,
    and then remove it from the lower rows. This should fix the problem. It can result
    in empty rows (since in my example we begin with 3 'rows' when there are only
    really 2), but these can simply be removed.
    """
    if sum([len(row) for row in rows]) == len(set(chain.from_iterable(rows))):
        # No elements are in multiple rows, return.
        return

    for element in elements:
        num_rows = sum(element in row for row in rows)
        if num_rows == 1:
            continue
        # If we reach here, we've found an element in multiple rows.

        rows_with_element = [row for row in rows if element in row]
        sorted_rows_with_element = sorted(
            rows_with_element,
            key=lambda row: (
                row[0].page_number,
                max(-(elem.bounding_box.y1) for elem in row),
            ),
        )
        # Remove the element from all but the first row.
        for row in sorted_rows_with_element[1:]:
            rows.remove(row)
            new_row = row.remove_element(element)
            if new_row:
                rows.add(new_row)


def _fix_cols(cols: Set["ElementList"], elements: "ElementList") -> None:
    """
    The same as _fix_rows, but when an element is in multiple columns, for example
    ---------
    | A | B |
    --------|
    |   C   |
    ---------
    """
    if sum([len(col) for col in cols]) == len(set(chain.from_iterable(cols))):
        # No elements are in multiple cols, return.
        return
    for element in elements:
        num_cols = sum(element in col for col in cols)
        if num_cols == 1:
            continue
        # If we reach here, we've found an element in multiple cols.

        cols_with_element = [col for col in cols if element in col]
        sorted_cols_with_element = sorted(
            cols_with_element, key=lambda col: max(elem.bounding_box.x0 for elem in col)
        )
        # Remove the element from all but the first col.
        for col in sorted_cols_with_element[1:]:
            cols.remove(col)
            new_col = col.remove_element(element)
            if new_col:
                cols.add(new_col)
    return
