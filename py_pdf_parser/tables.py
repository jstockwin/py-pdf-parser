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
    allow_gaps: bool = False,
    reference_element: Optional["PDFElement"] = None,
    tolerance: float = 0.0,
    remove_duplicate_header_rows: bool = False,
) -> List[List]:
    """
    Returns elements structured as a table.

    Given an ElementList, tries to extract a structured table by examining which
    elements are aligned.

    To use this function, there must be at least one full row and one full column (which
    we call the reference row and column), i.e. the reference row must have an element
    in every column, and the reference column must have an element in every row. The
    reference row and column can be specified by passing the single element in both the
    reference row and the reference column. By default, this is the top left element,
    which means we use the first row and column as the references. Note if you need to
    change the reference_element, that means you have gaps in your table, and as such
    you will need to pass `allow_gaps=True`.

    Important: This function uses the elements in the reference row and column to scan
    horizontally and vertically to find the rest of the table. If there are gaps in your
    reference row and column, this could result in rows and columns being missed by
    this function.

    There must be a clear gap between each row and between each column which contains no
    elements, and a single cell cannot contain multiple elements.

    If there are no valid reference rows or columns, try extract_table() instead. If you
    have elements spanning multiple rows or columns, it may be possible to fix this by
    using extract_table(). If you fail to satisfy any of the other conditions listed
    above, that case is not yet supported.

    Args:
        elements (ElementList): A list of elements to extract into a table.
        as_text (bool, optional): Whether to extract the text from each element instead
            of the PDFElement itself. Default: False.
        strip_text (bool, optional): Whether to strip the text for each element of the
                table (Only relevant if as_text is True). Default: True.
        allow_gaps (bool, optional): Whether to allow empty spaces in the table.
        reference_element (PDFElement, optional): An element in a full row and a full
            column. Will be used to specify the reference row and column. If None, the
            top left element will be used, meaning the top row and left column will be
            used. If there are gaps in these, you should specify a different reference.
            Default: None.
        tolerance (int, optional): For elements to be counted as in the same row or
            column, they must overlap by at least `tolerance`. Default: 0.
        remove_duplicate_header_rows (bool, optional): Remove duplicates of the header
            row (the first row) if they exist. Default: False.

    Raises:
        TableExtractionError: If something goes wrong.

    Returns:
        list[list]: a list of rows, which are lists of PDFElements or strings
            (depending on the value of as_text).
    """
    if reference_element is None:
        reference_element = elements[0]
    reference_row = elements.horizontally_in_line_with(
        reference_element, inclusive=True, tolerance=tolerance
    )
    reference_column = elements.vertically_in_line_with(
        reference_element, inclusive=True, tolerance=tolerance, all_pages=True
    )

    reference_columns = [
        elements.vertically_in_line_with(
            element, inclusive=True, tolerance=tolerance, all_pages=True
        )
        for element in reference_row
    ]
    reference_rows = [
        elements.horizontally_in_line_with(element, inclusive=True, tolerance=tolerance)
        for element in reference_column
    ]

    table: List[List] = []
    for current_row in reference_rows:
        row: List = []
        for current_column in reference_columns:
            element = current_row & current_column
            try:
                row.append(element.extract_single_element())
            except NoElementFoundError as err:
                if allow_gaps:
                    row.append(None)
                else:
                    raise TableExtractionError(
                        "Element not found, there appears to be a gap in the table. "
                        "If this is expected, pass allow_gaps=True."
                    ) from err
            except MultipleElementsFoundError as err:
                raise TableExtractionError(
                    "Multiple elements appear to be in the place of one cell in the "
                    "table. Please try extract_table() instead."
                ) from err
        table.append(row)

    table_size = sum(
        len([element for element in row if element is not None]) for row in table
    )
    if table_size != len(elements):
        raise TableExtractionError(
            f"Number of elements in table ({table_size}) does not match number of "
            f"elements passed ({len(elements)}). Perhaps try extract_table instead of "
            "extract_simple_table, or change you reference element."
        )

    if remove_duplicate_header_rows:
        table = _remove_duplicate_header_rows(table)

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
    remove_duplicate_header_rows: bool = False,
) -> List[List]:
    """
    Returns elements structured as a table.

    Given an ElementList, tries to extract a structured table by examining which
    elements are aligned. There must be a clear gap between each row and between each
    column which contains no elements, and a single cell cannot contain multiple
    elements.

    If you fail to satisfy any of the other conditions listed above, that case is not
    yet supported.

    Note: If you satisfy the conditions to use extract_simple_table, then that should be
    used instead, as it's much more efficient.

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
        remove_duplicate_header_rows (bool, optional): Remove duplicates of the header
            row (the first row) if they exist. Default: False.

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
        raise TableExtractionError(
            "An element is in multiple rows. If this is expected, you can try passing "
            "fix_element_in_multiple_rows=True"
        )
    if sum([len(col) for col in cols]) != len(set(chain.from_iterable(cols))):
        raise TableExtractionError(
            "An element is in multiple columns. If this is expected, you can try "
            "passing fix_element_in_multiple_cols=True"
        )

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

    if remove_duplicate_header_rows:
        table = _remove_duplicate_header_rows(table)

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
    if len(table) == 0:
        return []
    if header is None:
        header = table[0]
    elif len(header) != len(table[0]):
        raise InvalidTableHeaderError(
            f"Header length of {len(header)} does not match the width of the table "
            f"({len(table[0])})"
        )
    if len(header) != len(set(header)):
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

    sorted_rows = sorted(
        rows,
        key=lambda row: (
            row[0].page_number,
            max(-(elem.bounding_box.y1) for elem in row),
        ),
    )

    for element in elements:
        num_rows = sum(element in row for row in rows)
        if num_rows == 1:
            continue
        # If we reach here, we've found an element in multiple rows.

        rows_with_element = [row for row in rows if element in row]
        sorted_rows_with_element = sorted(
            rows_with_element, key=lambda row: sorted_rows.index(row)
        )
        # Remove the element from all but the first row.
        for row in sorted_rows_with_element[1:]:
            rows.remove(row)
            new_row = row.remove_element(element)
            if new_row:
                rows.add(new_row)
                # Update sorted rows
                sorted_rows = [
                    new_row if some_row == row else some_row for some_row in sorted_rows
                ]
            else:
                sorted_rows.remove(row)


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

    # We sort by looking at all the elements and choosing the element which starts
    # most to the right. The ones with elements which start most to the right
    # will be later on in the sorted list.
    sorted_columns = sorted(
        cols, key=lambda col: max(elem.bounding_box.x0 for elem in col)
    )
    for element in elements:
        num_cols = sum(element in col for col in cols)
        if num_cols == 1:
            continue
        # If we reach here, we've found an element in multiple cols.

        cols_with_element = [col for col in cols if element in col]
        sorted_cols_with_element = sorted(
            cols_with_element, key=lambda col: sorted_columns.index(col)
        )
        # Remove the element from all but the first col.
        for col in sorted_cols_with_element[1:]:
            cols.remove(col)
            new_col = col.remove_element(element)
            if new_col:
                cols.add(new_col)
                # Update sorted columns
                sorted_columns = [
                    new_col if some_col == col else some_col
                    for some_col in sorted_columns
                ]
            else:
                sorted_columns.remove(col)
    return


def _remove_duplicate_header_rows(table: List[List[Any]]) -> List[List[Any]]:
    """
    Removes rows which are duplicates of the header (i.e., the first) row.
    A row is considered duplicate if all of its elements have the same text and font of
    their correspondent elements (i.e., same index) in the header row.

    Args:
        table (List[List[Any]]): The table to remove the duplicate headers from.

    Returns:
        List[List[Any]]: The table without the duplicate header rows.
    """
    if len(table) <= 1:
        return table

    header = table[0]
    rows_without_duplicate_header = [
        row
        for row in table[1:]
        if any(
            not _are_elements_equal(element, header[index])
            for index, element in enumerate(row)
        )
    ]
    return [header] + rows_without_duplicate_header


def _are_elements_equal(
    elem_1: Optional["PDFElement"], elem_2: Optional["PDFElement"]
) -> bool:
    """
    Checks if two elements are equal.
    Two elements are considered equal if they are both None or they have the same text
    and font.

    Args:
        elem_1 (PDFElement, optional): The first element to compare.
        elem_2 (PDFElement, optional): The second element to compare.

    Returns:
        bool: True if elements are equal, False otherwise.
    """
    if elem_1 is None and elem_2 is None:
        return True

    if elem_1 is None or elem_2 is None:
        return False

    if elem_1.text() != elem_2.text() or elem_1.font != elem_2.font:
        return False

    return True
