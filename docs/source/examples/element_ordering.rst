.. _element-ordering:

Element Ordering
----------------

In this example, we see how to specify a custom ordering for the elements.

For this we will use a simple pdf, which has a single element in each corner of the
page. You can :download:`download the example here </example_files/grid.pdf>`.


Default
.......

The default element ordering is left to right, top to bottom.

.. code-block:: python

   from py_pdf_parser.loaders import load_file

   file_path = "grid.pdf"

   # Default - left to right, top to bottom
   document = load_file(file_path)
   print([element.text() for element in document.elements])

This results in
::

   ['Top Left', 'Top Right', 'Bottom Left', 'Bottom Right']

Presets
.......

There are also preset orderings for ``right to left, top to bottom``,
``top to bottom, left to right``, and ``top to bottom, right to left``. You can use
these by importing the :class:`~py_pdf_parser.components.ElementOrdering` class from
:py:mod:`py_pdf_parser.components` and passing these as the ``element_ordering``
argument to :class:`~py_pdf_parser.components.PDFDocument`. Note that keyword arguments
to :meth:`~py_pdf_parser.loaders.load` and :meth:`~py_pdf_parser.loaders.load_file` get
passed through to the :class:`~py_pdf_parser.components.PDFDocument`.

.. code-block:: python

   from py_pdf_parser.loaders import load_file
   from py_pdf_parser.components import ElementOrdering

   # Preset - right to left, top to bottom
   document = load_file(
       file_path, element_ordering=ElementOrdering.RIGHT_TO_LEFT_TOP_TO_BOTTOM
   )
   print([element.text() for element in document.elements])

   # Preset - top to bottom, left to right
   document = load_file(
       file_path, element_ordering=ElementOrdering.TOP_TO_BOTTOM_LEFT_TO_RIGHT
   )
   print([element.text() for element in document.elements])

   # Preset - top to bottom, right to left
   document = load_file(
       file_path, element_ordering=ElementOrdering.TOP_TO_BOTTOM_RIGHT_TO_LEFT
   )
   print([element.text() for element in document.elements])

which results in

::

   ['Top Right', 'Top Left', 'Bottom Right', 'Bottom Left']
   ['Bottom Left', 'Top Left', 'Bottom Right', 'Top Right']
   ['Top Right', 'Bottom Right', 'Top Left', 'Bottom Left']

Custom Ordering
...............

If none of the presets give an ordering you are looking for, you can also pass a
callable as the ``element_ordering`` argument of
:class:`~py_pdf_parser.components.PDFDocument`. This callable will be given a list of
elements for each page, and should return a list of the same elements, in the desired
order.

.. important::

   The elements which get passed to your function will be PDFMiner.six elements, and NOT
   class :class:`~py_pdf_parser.componenets.PDFElement`. You can access the ``x0``,
   ``x1``, ``y0``, ``y1`` directly, and extract the text using `get_text()`. Other
   options are available: please familiarise yourself with the PDFMiner.six
   documentation.

.. note::

   Your function will be called multiple times, once for each page of the document.
   Elements will always be considered in order of increasing page number, your function
   only controls the ordering within each page.

For example, if we wanted to implement an ordering which is bottom to top, left to right
then we can do this as follows:

.. code-block:: python

   from py_pdf_parser.loaders import load_file

   # Custom - bottom to top, left to right
   def ordering_function(elements):
       """
       Note: Elements will be PDFMiner.six elements. The x axis is positive as you go left
       to right, and the y axis is positive as you go bottom to top, and hence we can
       simply sort according to this.
       """
       return sorted(elements, key=lambda elem: (elem.x0, elem.y0))


   document = load_file(file_path, element_ordering=ordering_function)
   print([element.text() for element in document.elements])

which results in

::

   ['Bottom Left', 'Top Left', 'Bottom Right', 'Top Right']

Multiple Columns
................

Finally, suppose our PDF has multiple columns, like
:download:`this example </example_files/columns.pdf>`.

If we don't specify an ``element_ordering``, the elements will be extracted in the
following order:

::

   ['Column 1 Title', 'Column 2 Title', 'Here is some column 1 text.', 'Here is some column 2 text.', 'Col 1 left', 'Col 1 right', 'Col 2 left', 'Col 2 right']

If we visualise this document
(see the :ref:`simple-memo` example if you don't know how to do this), then we can see
that the column divider is at an ``x`` value of about 300. Using this information, we
can specify a custom ordering function which will order the elements left to right,
top to bottom, but in each column individually.

.. code-block:: python

   from py_pdf_parser.loaders import load_file

   document = load_file("columns.pdf")

   def column_ordering_function(elements):
       """
       The first entry in the key is False for colum 1, and Tru for column 2. The second
       and third keys just give left to right, top to bottom.
       """
       return sorted(elements, key=lambda elem: (elem.x0 > 300, -elem.y0, elem.x0))


   document = load_file(file_path, element_ordering=column_ordering_function)
   print([element.text() for element in document.elements])

which returns the elements in the correct order:

::

   ['Column 1 Title', 'Here is some column 1 text.', 'Col 1 left', 'Col 1 right', 'Column 2 Title', 'Here is some column 2 text.', 'Col 2 left', 'Col 2 right']
