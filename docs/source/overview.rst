Overview
========

Introduction
------------

This PDF Parser is a tool built on top of PDF Miner to help extracting information from PDFs in Python. The main idea was to create a tool that could be driven by code to interact with the elements on the PDF and slowly classify them by creating sections and adding tags to them. It also comes with a helpful visualisation tool which enables you to examine the current status of your elements.

This page gives a brief overview of the PDF Parser, but there is also a full :doc:`reference/index` of all the functionality. You may get a more in-depth overview by looking at the :doc:`examples/index`.

Setup
-----

You will need to have Python 3.6 or greater installed, and if you're installing the development requirements to use the visualise tool you will also need tkinter installed on your system. For information on how to do this, see https://tkdocs.com/tutorial/install.html.

We recommend you install the development requirements with ``pip3 install py-pdf-parser[dev]``, which enables the visualise tool. If you don't need the visualise tool (for example in a production app once you've written your parsing scripts) you can simply run ``pip3 install py-pdf-parser``.

When Should I Use Py PDF Parser?
--------------------------------

Py PDF Parser is best suited to locating and extracting specific data in a structured way from a PDF. You can locate contents however you want (by text, location, font, etc), and since it is code-driven you have the flexibility to implement custom logic without having to deal with the PDF itself. Py pdf parser helps to abstract away things like page breaks (unless you want to use them), which helps to write robust code which will extract data from multiple PDFs of the same type, even if there are differences between each individual document.

Py PDF Parser is good at extracting tables in PDFs, and allows you to write code to programmatically locate the tables to extract. Page breaks (and even headers or footers) half way through your table can be ignored easily. If you're trying to extract all tables from a PDF, other tools (e.g. https://camelot-py.readthedocs.io/en/master/) are available and may be more appropriate.

If you're simply trying to extract all of the text from a PDF, other tools (e.g. https://textract.readthedocs.io/en/stable/python_package.html) may be more appropriate. Whilst you can still do this with Py PDF Parser, it is not designed to be a tool where you simply plug in a PDF and it spits it out in text format. Py PDF Parser is not a plug-and-play solution, but rather a tool to help you write code that extracts certain pieces of data from a structured PDF.

Loading A PDF
-------------

To load a PDF, use the :func:`~py_pdf_parser.loaders.load_file`: function from the :doc:`reference/loaders`. You will need to use :func:`~py_pdf_parser.loaders.load_file`: with a file path to be able to use the visualisation tool with your PDF as the background. If you don't have this, you can instead use the :func:`~py_pdf_parser.loaders.load`: function, but when you use the visualisation tool there will be no background.

We order the elements in a pdf, left-to-right, top-to-bottom. At the moment, this is not configurable. Each :class:`~py_pdf_parser.components.PDFElement` within the :class:`~py_pdf_parser.components.PDFDocument` are aware of their position, both on the page and within the document, and also have properties allowing you to access their font and text. For more information about :class:`~py_pdf_parser.components.PDFDocument` and :class:`~py_pdf_parser.components.PDFElement`, see :doc:`reference/components`.

Pay particular attention to the ``la_params`` argument. These will need to be fine-tuned for your PDF. We suggest immediately visualising your PDF using the visualisation tool to see how the elements have been grouped. If multiple elements have been counted as one, or vice versa, you should be able to fix this by tweaking the ``la_params``.

Filtering
---------

Once you have loaded your PDF, say into a variable :class:`document<py_pdf_parser.components.PDFDocument>`, you can start interacting with the elements. You can access all the elements by calling :class:`document.elements<py_pdf_parser.filtering.ElementList>`. You may now want to filter your elements, for example you could do :meth:`document.elements.filter_by_text_equal("foo")<py_pdf_parser.filtering.ElementList.filter_by_text_equal>` to filter for all elements which say "foo". To view all available filters, have a look at the :doc:`reference/filtering` reference.

The :class:`document.elements<py_pdf_parser.filtering.ElementList>` object, and any filtered subset thereof, will be an :class:`~py_pdf_parser.filtering.ElementList`. These act like sets of elements, and so you can union (:meth:`|<py_pdf_parser.filtering.ElementList.__or__>`), intersect (:meth:`&<py_pdf_parser.filtering.ElementList.__and__>`), difference (:meth:`-<py_pdf_parser.filtering.ElementList.__sub__>`) and symmetric difference (:meth:`^<py_pdf_parser.filtering.ElementList.__xor__>`) different filtered sets of elements.

You can also chain filters, which will do the same as intersecting multiple filters, for example ``document.elements.filter_by_text_equal("foo").filter_by_tag("bar")`` is the same as ``document.elements.filter_by_text_equal("foo") & document.elements.filter_by_tag("bar")``.

If you believe you have filtered down to a single element, and would like to examine that element, you can call :meth:`~py_pdf_parser.filtering.ElementList.extract_single_element`. This will return said element, or raise an exception if there is not a single element in your list.

You can see an example of filtering in the :ref:`simple-memo` example.

Classifying Elements
--------------------

There are three ways to classify elements:

- add tags
- create sections
- mark certain elements as ignored

To add a tag, you can simply call :meth:`~py_pdf_parser.components.PDFElement.add_tag` on an :class:`~py_pdf_parser.components.PDFElement`, or :meth:`~py_pdf_parser.filtering.ElementList.add_tag_to_elements` on an :class:`~py_pdf_parser.filtering.ElementList`. You can filter by tags.

To create a section, you can call :meth:`~py_pdf_parser.sectioning.Sectioning.create_section`. See :doc:`reference/sectioning` for more information and the :ref:`order-summary` example for an example. When you create a section you simply specify a name for the section, and the start and end element for the section. Any elements between the start and end element will be included in your section. You can add multiple sections with the same name, and internally they will be given unique names. You can filter by either the non-unique ``section_name``, or by the unique sections. Elements can be in multiple sections.

To mark an element as ignored, simply set the ``ignore`` property to ``True``. Ignored elements will not be included in any :class:`~py_pdf_parser.filtering.ElementList`, however existing lists which you have assigned to variables will not be re-calculated and so may still include the ignored elements.

To process a whole pdf, we suggest that you mark any elements you're not interested in as ignored, group any elements which are together into sections, and then add tags to important elements. You can then loop through filtered sets of elements to extract the information you would like.

Visualisation Tool
------------------

The PDF Parser comes with a visualisation tool. See the :doc:`reference/visualise` documentation. When you visualise your :class:`~py_pdf_parser.components.PDFDocument`, you'll be able to see each page of the document in turn, with every :class:`~py_pdf_parser.components.PDFElement` highlighted. You can hover over the elements to see their sections, tags and whether they are ignored or not. This is very helpful for debugging any problems.

You can use the arrow key icons to change page, and can press home to return to page 1. You can also use the scroll wheel on your mouse to zoom in and out.

You can see an example of the visualisation in the :ref:`simple-memo` and :ref:`order-summary` examples.

Font Mappings
-------------

You can filter elements by font. The font will be taken from the PDF itself, however often they have long and confusing names. You can specify a ``font_mapping`` when you load the document to map these to more memorable names. See the :doc:`reference/components` reference for the :class:`~py_pdf_parser.components.PDFDocument` arguments for more information.

You can see an example of font mapping in the :ref:`order-summary` example.

Tables
------

We have many functions to help extract tables. All of these use the positioning of the elements on the page to do this. See the :doc:`reference/tables` reference, and the :ref:`order-summary` and :ref:`more-tables` examples.
