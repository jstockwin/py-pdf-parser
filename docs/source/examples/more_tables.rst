.. _more-tables:

More Tables
-----------

In this example, we will learn how to extract different types of table, and the difference between a simple table and more complicated ones.

You can :download:`download the example here </example_files/tables.pdf>`.

Please read the :ref:`order-summary` example first, as this covers some other functionality of the table extraction methods.

Load the file
.............

The following code (click "show code" below to see it) loads the file, and assigns the elements for each table to a variable. If this does not make sense, you should go back and look at some of the previous examples.

.. raw:: html

   <details>
   <summary><a>Show code</a></summary>

.. code-block:: python

   from py_pdf_parser.loaders import load_file

   FONT_MAPPING = {
       "BAAAAA+LiberationSerif-Bold,12.0": "header",
       "CAAAAA+LiberationSerif,12.0": "table_element",
   }
   document = load_file("tables.pdf", font_mapping=FONT_MAPPING)

   headers = document.elements.filter_by_font("header")

   # Extract reference elements
   simple_table_header = headers.filter_by_text_equal(
       "Simple Table"
   ).extract_single_element()

   simple_table_with_gaps_header = headers.filter_by_text_equal(
       "Simple Table with gaps"
   ).extract_single_element()

   simple_table_with_gaps_in_first_row_col_header = headers.filter_by_text_equal(
       "Simple Table with gaps in first row/col"
   ).extract_single_element()

   non_simple_table_header = headers.filter_by_text_equal(
       "Non Simple Table"
   ).extract_single_element()

   non_simple_table_with_merged_cols_header = headers.filter_by_text_equal(
       "Non Simple Table with Merged Columns"
   ).extract_single_element()

   non_simple_table_with_merged_rows_header = headers.filter_by_text_equal(
       "Non Simple Table with Merged Rows and Columns"
   ).extract_single_element()

   over_the_page_header = headers.filter_by_text_equal(
       "Over the page"
   ).extract_single_element()

   # Extract table elements
   simple_table_elements = document.elements.between(
       simple_table_header, simple_table_with_gaps_header
   )
   simple_table_with_gaps_elements = document.elements.between(
       simple_table_with_gaps_header, simple_table_with_gaps_in_first_row_col_header
   )

   simple_table_with_gaps_in_first_row_col_elements = document.elements.between(
       simple_table_with_gaps_in_first_row_col_header, non_simple_table_header
   )

   non_simple_table_elements = document.elements.between(
       non_simple_table_header, non_simple_table_with_merged_cols_header
   )

   non_simple_table_with_merged_cols_elements = document.elements.between(
       non_simple_table_with_merged_cols_header, non_simple_table_with_merged_rows_header
   )

   non_simple_table_with_merged_rows_and_cols_elements = document.elements.between(
       non_simple_table_with_merged_rows_header, over_the_page_header
   )

   over_the_page_elements = document.elements.after(over_the_page_header)

.. raw:: html

   </details>

Overview
........

The tables in the example pdf are split into "Simple Tables" and "Non Simple Tables". For the simple tables, we will be able to use :meth:`~py_pdf_parser.tables.extract_simple_table`, otherwise we must use :meth:`~py_pdf_parser.tables.extract_table`. The former is much more efficient, and should be used when possible.

In general, tables can become more complicated by having missing cells, or merged cells which go across multiple columns or multiple rows. In both cases, you will have to pass additional parameters to stop exceptions being raised when this is the case. This is to make the extraction more robust, and protect against unexpected outcomes.

To use :meth:`~py_pdf_parser.tables.extract_simple_table` we must have at least one column and one row which have no missing cells, and we must have no merged cells at all. We will need to know which row/column has no missing cells, as these must be passed as the reference row and column.

To understand why: for each column element in the reference row and each row element in the reference column, :meth:`~py_pdf_parser.tables.extract_simple_table` will scan across from the row element (to get the row) and up/down from the column element (to get the column), and see if there is an element there. If there is, it is added to the table. Therefore, if there are gaps in the reference row/column, other elements may get missed. There is a check for this, so an exception will be raised if this is the case.

This means :meth:`~py_pdf_parser.tables.extract_simple_table` takes time proportional to ``len(cols) + len(rows)``. Conversely,  :meth:`~py_pdf_parser.tables.extract_table` is at least ``len(cols) * len(rows)``, and if there are merged cells it will be even worse. (Note in reality the complexity is not quite this simple, but it should give you an idea of the difference.)

Below, we will work through increasingly complex examples to explain the functionality, and the steps involved.

Simple Table
............

This table is as simple as they come - there are no blank or merged cells. This means we can simply use :meth:`~py_pdf_parser.tables.extract_simple_table` as we have seen previously.

.. code-block:: python

   from py_pdf_parser import tables
   table = tables.extract_simple_table(simple_table_elements, as_text=True)

::

   >>> table
   [['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4'], ['A', '1', 'A', '1'], ['B', '2', 'B', '2'], ['C', '3', 'C', '3']]

Simple Table with gaps
......................

This table has gaps, however there are no gaps in the first row or column. These are the default reference row and column, and so :meth:`~py_pdf_parser.tables.extract_simple_table` will still work as expected. Blank cells will be empty strings if ``as_text=True``, and otherwise they will be ``None``. However, if we try the same code as above:

.. code-block:: python

   table = tables.extract_simple_table(
       simple_table_with_gaps_elements, as_text=True
   )

this will raise an exception:

::

   py_pdf_parser.exceptions.TableExtractionError: Element not found, there appears to be a gap in the table. If this is expected, pass allow_gaps=True.

This is to allow py-pdf-parser to be more robust in the case that you're expecting your table to have no empty cells. As the error message says, since this is expected behaviour we can simply pass ``allow_gaps=True``.

.. code-block:: python

   table = tables.extract_simple_table(
       simple_table_with_gaps_elements, as_text=True, allow_gaps=True
   )

::

   >>> table
   [['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4'], ['A', '1', '', '1'], ['B', '', '', ''], ['C', '', 'C', '3']]

Simple Table with gaps in first row/col
.......................................

This table is similar to the above example, but now we have gaps in the first row and the first column (if either of these were true then the above wouldn't work). If we try the above code, a useful exception is raised:

.. code-block:: python

   table = tables.extract_simple_table(
       simple_table_with_gaps_in_first_row_col_elements, as_text=True, allow_gaps=True
   )

::

   py_pdf_parser.exceptions.TableExtractionError: Number of elements in table (9) does not match number of elements passed (12). Perhaps try extract_table instead of extract_simple_table, or change you reference element.

The error message suggests either passing another reference element, or using the more complicated :meth:`~py_pdf_parser.tables.extract_table` method. In this case, as we still have a row and a column which have no missing cells, we can just pass a new reference element.

As such, we can use the second column and the last row as our references, as neither of these have missing cells. The reference row and column are specified by simply passing the unique element in both the reference row and the reference column (called the reference element). In this case, it's the first number "3" in the table. Here we will be lazy and simply use the fact that this is the 10th element in the table, but you should probably do something smarter.

.. code-block:: python

   reference_element = simple_table_with_gaps_in_first_row_col_elements[9]
   table = tables.extract_simple_table(
       simple_table_with_gaps_in_first_row_col_elements,
       as_text=True,
       allow_gaps=True,
       reference_element=reference_element,
   )

::

    >>> table
    [['Heading 1', 'Heading 2', '', 'Heading 4'], ['', '1', 'A', ''], ['B', '2', '', '2'], ['C', '3', 'C', '3']]

Non Simple Table
................

The next table does not have any row with no empty cells, and as such we must use :meth:`~py_pdf_parser.tables.extract_table`. There is no ``allow_gaps`` parameter for this method, since if you don't want to allow gaps you should be using :meth:`~py_pdf_parser.tables.extract_simple_table` instead.

Whilst the below may seem easier than working out the reference element in the above example, please note that it will be computationally slower.

.. code-block:: python

   table = tables.extract_table(non_simple_table_elements, as_text=True)

::

   >>> table
   [['', 'Heading 2', 'Heading 3', 'Heading 4'], ['A', '1', '', '1'], ['B', '', 'B', '2'], ['C', '3', 'C', '']]


Non Simple Table with Merged Columns
....................................

This table has text which goes across multiple columns. If we naively run this as above:

.. code-block:: python

   table = tables.extract_table(non_simple_table_with_merged_cols_elements, as_text=True)

then we get an exception:

::

   py_pdf_parser.exceptions.TableExtractionError: An element is in multiple columns. If this is expected, you can try passing fix_element_in_multiple_cols=True

Just like ``allow_gaps``, this is so we can be more robust in the case that this is not expected. The error helpfully suggests to try passing ``fix_element_in_multiple_cols=True``.

.. code-block:: python

   table = tables.extract_table(
       non_simple_table_with_merged_cols_elements,
       as_text=True,
       fix_element_in_multiple_cols=True,
   )

::

   >>> table
   [['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4'], ['A', '1', 'A', '1'], ['This text spans across multiple columns', '', 'B', '2'], ['C', '3', 'C', '3']]

Note that the merged cell has been pushed into the left-most column. Likewise, if we had a cell that was merged across multiple rows, we could pass ``fix_element_in_multiple_rows=True``, and it would be pushed into the top row.

Non Simple Table with Merged Rows and Columns
.............................................

In this case we have both merged rows and merged columns. We can pass both ``fix_element_in_multiple_rows=True`` and ``fix_element_in_multiple_cols=True``. The merged cell will be pushed into the left-most column and the top row.

.. code-block:: python

   table = tables.extract_table(
       non_simple_table_with_merged_rows_and_cols_elements,
       as_text=True,
       fix_element_in_multiple_rows=True,
       fix_element_in_multiple_cols=True,
   )

::

   >>> table
   [['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4'], ['This text spans across multiple rows and \nmultiple columns.', '', 'A', '1'], ['', '', 'B', '2'], ['C', '3', 'C', '3']]


Over the page
.............

The final table goes over the page break. This is not a problem, simply pass the elements within the table and the result should be correct.

If you had e.g. a footer that broke the table in two, simply ensure these elements are not included in the element list you pass to :meth:`~py_pdf_parser.tables.extract_table`, and again it should still work.

.. code-block:: python

   table = tables.extract_simple_table(over_the_page_elements, as_text=True)

::

   >>> table
   [['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4'], ['A', '1', 'A', '1'], ['B', '2', 'B', '2'], ['C', '3', 'C', '3']]
