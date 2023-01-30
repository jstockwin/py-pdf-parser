.. _order-summary:

Order Summary
-------------

In this example we will extract some tabular data from an order summary pdf.

You can :download:`download the example here </example_files/order_summary.pdf>`.

This is a fairly simple PDF, and as such it would be fairly easy to identify the tables and extract the data from them, however we will use this example to introduce font mappings and sections, which will come in useful for larger PDFs.

Step 1 - Load the file
......................

We can :func:`load <py_pdf_parser.loaders.load_file>` the file as follows, and take a quick look using the :func:`visualise tool <py_pdf_parser.visualise.main.visualise>` to check it looks good.

.. code-block:: python

   from py_pdf_parser.loaders import load_file
   from py_pdf_parser.visualise import visualise

   document = load_file("order_summary.pdf")
   visualise(document)

This should show the following. We should check that py-pdf-parser has detected each element correctly, which in this case it has.

.. image:: /screenshots/order_summary_example/initial.png
   :height: 300px

Step 2 - Use a font mapping
...........................

Each :class:`~py_pdf_parser.components.PDFElement` has a :attr:`~py_pdf_parser.components.PDFElement.font` property, which is the name of the font in the PDF document (including the font size). You can use fonts to help filter elements.

Fonts often have long, not very useful names. However, additional keyword arguments passed to :func:`~py_pdf_parser.loaders.load_file` will be used to initialise the :class:`~py_pdf_parser.components.PDFDocument`. One of these is the font mapping, which allows you to map the fonts in your PDF to more useful names.

The visualise tool allows you to inspect fonts. If you hover over an element, a summary will be shown in text at the bottom of the window. For example, in the image below we hover over the first cell in the table, and can see that the font is ``EAAAA+FreeMono,12.0``.

.. image:: /screenshots/order_summary_example/showing_font_1.png
   :height: 300px

We can easily ask to see all of the available fonts by running

::

    >>> set(element.font for element in document.elements)
    {'EAAAAA+FreeMono,12.0', 'BAAAAA+LiberationSerif-Bold,16.0', 'CAAAAA+LiberationSerif,12.0', 'DAAAAA+FreeMonoBold,12.0', 'BAAAAA+LiberationSerif-Bold,12.0'}

Using this and the visualise tool, we can now choose better names for each of the fonts, and then load the document again, but this time providing a font mapping.

.. code-block:: python

   FONT_MAPPING = {
       "BAAAAA+LiberationSerif-Bold,16.0": "title",
       "BAAAAA+LiberationSerif-Bold,12.0": "sub_title",
       "CAAAAA+LiberationSerif,12.0": "text",
       "DAAAAA+FreeMonoBold,12.0": "table_header",
       "EAAAAA+FreeMono,12.0": "table_text",
   }
   document = load_file("order_summary.pdf", font_mapping=FONT_MAPPING)

Using the visualise tool again, we can now see that our element's font has changed to ``table_text``, which is a much more useful name for us.

.. image:: /screenshots/order_summary_example/showing_font_2.png
   :height: 300px

Step 3 - Use regex for font mapping
...................................
In certain use cases (especially when handling many PDF files) you may encounter the problem that the same fonts have different prefixes.

For example:

File 1:
::

    >>> set(element.font for element in document.elements)
    {'EAAAAA+FreeMono,12.0', 'BAAAAA+LiberationSerif-Bold,16.0', 'CAAAAA+LiberationSerif,12.0', 'DAAAAA+FreeMonoBold,12.0', 'BAAAAA+LiberationSerif-Bold,12.0'}

File 2:
::

    >>> set(element.font for element in document.elements)
    {'CIPKDS+FreeMono,12.0', 'FDHZTR+LiberationSerif-Bold,16.0', 'KJVFSL+LiberationSerif,12.0', 'BXNKHF+FreeMonoBold,12.0', 'OKSDFT+LiberationSerif-Bold,12.0'}

In this case mapping fonts with regex patterns makes more sense. Create the your font mapping like before but fill it with regex patterns that don't specify the prefix precisely. Also specify that the font mapping contains regex patterns when loading the document.

.. code-block:: python

   FONT_MAPPING = {
       r"\w{6}\+LiberationSerif-Bold,16.0": "title",
       r"\w{6}\+LiberationSerif-Bold,12.0": "sub_title",
       r"\w{6}\+LiberationSerif,12.0": "text",
       r"\w{6}\+FreeMonoBold,12.0": "table_header",
       r"\w{6}\+FreeMono,12.0": "table_text",
   }
   document = load_file("order_summary.pdf", font_mapping=FONT_MAPPING, font_mapping_is_regex=True)

Step 4 - Add sections
.....................

Another thing we can do to make our job easier is to add :class:`Sections<py_pdf_parser.sectioning.Section>` to our document. A :class:`Sections<py_pdf_parser.sectioning.Sectioning>` class is made available on :attr:`document.sectioning<py_pdf_parser.components.PDFDocument.sectioning>`, which in particular allows us to call :meth:`~py_pdf_parser.sectioning.Sectioning.create_section`.

A section has a name, and contains all elements between the start element and the end element. You can add multiple sections with the same name, but each section will have both a ``name`` and a ``unique_name`` (which is just the name with an additional ``_n`` on the end, where ``n`` is the number of sections with that name).

As with the :class:`~py_pdf_parser.components.PDFDocument`, a :class:`~py_pdf_parser.sectioning.Section` has an :attr:`~py_pdf_parser.sectioning.Section.elements` property which returns an :class:`~py_pdf_parser.filtering.ElementList`, allowing you to filter the elements.

.. important:: Never instantiate a :class:`Sections<py_pdf_parser.sectioning.Section>` yourself. You should always use :meth:`~py_pdf_parser.sectioning.Sectioning.create_section`.

Calling :meth:`~py_pdf_parser.sectioning.Sectioning.create_section` will return the :class:`~py_pdf_parser.sectioning.Section`, but the :class:`~py_pdf_parser.sectioning.Sectioning` class also has :meth:`~py_pdf_parser.sectioning.Sectioning.get_section` and :meth:`~py_pdf_parser.sectioning.Sectioning.get_sections_with_name` methods.

Going back to our example, we will create sections for the order summary table, and for the totals table. Our order summary table will start with the "Order Summary:" sub title and end at the "Totals:" sub title. Note that there are two elements on the page with text equal to "Order Summary:", however they have different font and so we can still extract exactly the one we want.


.. image:: /screenshots/order_summary_example/zoomed.png
   :height: 300px

By default, :meth:`~py_pdf_parser.sectioning.Sectioning.create_section` will include the last element in the section, but this can be disabled by passing ``include_last_element=False``.

The totals section will run from the "Totals:" sub title, until the end of the document. An :class:`~py_pdf_parser.filtering.ElementList` (e.g. ``document.elements``) acts like a set of elements, but it does also define an order, and as such we can access the last element in the :class:`~py_pdf_parser.filtering.ElementList` by simply doing ``document.elements[-1]``.

.. code-block:: python

   order_summary_sub_title_element = (
       document.elements.filter_by_font("sub_title")
       .filter_by_text_equal("Order Summary:")
       .extract_single_element()
   )

   totals_sub_title_element = (
       document.elements.filter_by_font("sub_title")
       .filter_by_text_equal("Totals:")
       .extract_single_element()
   )

   final_element = document.elements[-1]

   order_summary_section = document.sectioning.create_section(
       name="order_summary",
       start_element=order_summary_sub_title_element,
       end_element=totals_sub_title_element,
       include_last_element=False,
   )

Again, the visualise tool is helpful to check everything worked as expected, as it will draw a border around all of our sections:

.. image:: /screenshots/order_summary_example/sections.png
   :height: 300px

Step 5 - Extract tables
.......................

Now we have mapped our fonts and added some sections, we'd like to extract the table. In this case, we are able to use :meth:`~py_pdf_parser.tables.extract_simple_table`. We need to pass this the elements which form our table, however currently our sections also include the sub titles, "Order Summary:" and "Totals:". We need to exclude these from the elements we pass to :meth:`~py_pdf_parser.tables.extract_simple_table`. We have a reference to the sub title elements, so we could simply use :meth:`~py_pdf_parser.filtering.ElementList.remove_element`. However, since the tables seem to have their own fonts, it may be more robust to use :meth:`~py_pdf_parser.filtering.ElementList.filter_by_fonts`.

We will also pass ``as_text=True``, since we are interested in the text, not the :class:`PDFElements<py_pdf_parser.components.PDFElement>` themselves.

.. code-block:: python

   order_summary_table = tables.extract_simple_table(
       order_summary_section.elements.filter_by_fonts("table_header", "table_text"),
       as_text=True,
   )

   totals_table = tables.extract_simple_table(
       totals_section.elements.filter_by_fonts("table_header", "table_text"), as_text=True
   )

This gives:

::

   >>> order_summary_table
   [['Item', 'Unit Cost', 'Quantity', 'Cost'], ['Challenger 100g\nWhole Hops', '£3.29', '1', '£3.29'], ['Maris Otter \nPale Ale Malt \n(Crushed)', '£1.50/1000g', '4000g', '£6.00'], ['WLP037 \nYorkshire Ale \nYeast', '£7.08', '1', '£7.08'], ['Bottle Caps', '£1 per 100', '500', '£5']]

   >>> totals_table
   [['Subtotal:', '£26.28'], ['Shipping', '£6'], ['VAT 20%', '£6.45'], ['Total:', '£38.73']]

As one final step, since the order summary table has a header row, we can make use of :meth:`~py_pdf_parser.tables.add_header_to_table`, which will change the list of lists to a list of dicts, mapping the header to the values in each row:

.. code-block:: python

   order_summary_with_header = tables.add_header_to_table(order_summary_table)

::

   >>> order_summary_with_header
   [{'Item': 'Challenger 100g\nWhole Hops', 'Unit Cost': '£3.29', 'Quantity': '1', 'Cost': '£3.29'}, {'Item': 'Maris Otter \nPale Ale Malt \n(Crushed)', 'Unit Cost': '£1.50/1000g', 'Quantity': '4000g', 'Cost': '£6.00'}, {'Item': 'WLP037 \nYorkshire Ale \nYeast', 'Unit Cost': '£7.08', 'Quantity': '1', 'Cost': '£7.08'}, {'Item': 'Bottle Caps', 'Unit Cost': '£1 per 100', 'Quantity': '500', 'Cost': '£5'}]


Full Code
.........

.. code-block:: python

   from py_pdf_parser.loaders import load_file
   from py_pdf_parser import tables

   # from py_pdf_parser.visualise import visualise


   # Step 1 - Load the file
   document = load_file("order_summary.pdf")

   # visualise(document)

   # Step 2 - Use a font mapping

   # Show all fonts:
   # set(element.font for element in document.elements)

   FONT_MAPPING = {
       "BAAAAA+LiberationSerif-Bold,16.0": "title",
       "BAAAAA+LiberationSerif-Bold,12.0": "sub_title",
       "CAAAAA+LiberationSerif,12.0": "text",
       "DAAAAA+FreeMonoBold,12.0": "table_header",
       "EAAAAA+FreeMono,12.0": "table_text",
   }
   document = load_file("order_summary.pdf", font_mapping=FONT_MAPPING)

   # OR

   # use regex patterns

   FONT_MAPPING = {
       r"\w{6}\+LiberationSerif-Bold,16.0": "title",
       r"\w{6}\+LiberationSerif-Bold,12.0": "sub_title",
       r"\w{6}\+LiberationSerif,12.0": "text",
       r"\w{6}\+FreeMonoBold,12.0": "table_header",
       r"\w{6}\+FreeMono,12.0": "table_text",
   }
   document = load_file("order_summary.pdf", font_mapping=FONT_MAPPING, font_mapping_is_regex=True)

   # visualise(document)

   # Step 3 - Add sections
   order_summary_sub_title_element = (
       document.elements.filter_by_font("sub_title")
       .filter_by_text_equal("Order Summary:")
       .extract_single_element()
   )

   totals_sub_title_element = (
       document.elements.filter_by_font("sub_title")
       .filter_by_text_equal("Totals:")
       .extract_single_element()
   )

   final_element = document.elements[-1]

   order_summary_section = document.sectioning.create_section(
       name="order_summary",
       start_element=order_summary_sub_title_element,
       end_element=totals_sub_title_element,
       include_last_element=False,
   )

   totals_section = document.sectioning.create_section(
       name="totals", start_element=totals_sub_title_element, end_element=final_element
   )

   # visualise(document)

   # Step 4 - Extract tables

   order_summary_table = tables.extract_simple_table(
       order_summary_section.elements.filter_by_fonts("table_header", "table_text"),
       as_text=True,
   )

   totals_table = tables.extract_simple_table(
       totals_section.elements.filter_by_fonts("table_header", "table_text"), as_text=True
   )

   order_summary_with_header = tables.add_header_to_table(order_summary_table)
