Overview
========

Introduction
------------

This PDF Parser is a tool built on top of PDF Miner to help extracting information from
PDFs in Python. The main idea was to create a tool that could be driven by code to
interact with the elements on the PDF and slowly classify them by creating sections
and adding tags to them. It also comes with a helpful visualisation tool which enables
you to examine the current status of your elements.

This page gives a brief overview of the PDF Parser, but there is also a full
:doc:`reference/index` of all the functionality.

Setup
-----

At the moment you will need to install it from github. You will also need to manually
install matplotlib and PyQt5 using apt. We are working on this.

Loading A PDF
-------------

To load a PDF, use the ``load_file`` function from the :doc:`reference/loaders`. You
will need to use ``load_file`` with a file path to be able to use the visualisation
tool with your PDF as the background. If you don't have this, you can instead use the
``load`` function, but when you use the visualisation tool there will be no background.

We order the elements in a pdf, left-to-right, top-to-bottom. At the moment, this is
not configurable. Each ``PDFElement`` within the ``PDFDocument`` are aware of their
position, both on the page and within the document, and also have properties allowing
you to access their font and text. For more information about ``PDFDocument`` and
``PDFElement``, see :doc:`reference/components`.

Pay particular attention to the ``la_params`` argument. These will need to be
fine-tuned for your PDF. We suggest immediately visualising your PDF using the
visualisation tool to see how the elements have been grouped. If multiple elements
have been counted as one, or vice versa, you should be able to fix this by tweaking
the ``la_params``.

Filtering
---------

Once you have loaded your PDF, say into a variable ``document``, you can start
interacting with the elements. You can access all the elements by calling
``document.elements``. You may now want to filter your elements, for example you could
do ``document.elements.filter_by_text_equal("foo")`` to filter for all elements which
say "foo". To view all available filters, have a look at the :doc:`reference/filtering`
reference.

The ``document.elements`` object, and any filtered subset thereof, will be an
``ElementList``. These act like sets of elements, and so you can union (``|``),
intersect (``&``), difference (``-``) and symmetric difference (``^``) different
filtered sets of elements.

You can also chain filters, which will do the same as intersecting multiple filters, for
example ``document.elements.filter_by_text_equal("foo").filter_by_tag("bar")`` is the
same as ``document.elements.filter_by_text_equal("foo") &
document.elements.filter_by_tag("bar")``.

If you believe you have filtered down to a single element, and would like to examine
that element, you can call ``extract_single_element`` on your ``ElementList``. This will
return said element, or raise an exception if there is not a single element in your
list.

Classifying Elements
--------------------

There are three ways to classify elements:

- add tags
- create sections
- mark certain elements as ignored

To add a tag, you can simply call ``add_tag`` on an element. You can filter by tags.

To create a section, you can call ``document.sectioning.create_section``. See
:doc:`reference/sectioning` for more information. When you create a section you simply
specify a name for the section, and the start and end element for the section. Any
elements between the start and end element will be included in your section. You can
add multiple sections with the same name, and internally they will be given unique
names. You can filter by either the non-unique ``section_name``, or by the unique
sections. Elements can be in multiple sections.

To mark an element as ignored, simply set the ``ignore`` property to ``True``. You can
then remove all ignored elements by doing ``document.elements.exclude_ignored()``.

To process a whole pdf, we suggest that you mark any elements you're not interested in
as ignored, group any elements which are together into sections, and then add tags to
important elements. You can then loop through filtered sets of elements to extract the
information you would like.

Visualisation Tool
------------------

The PDF Parser comes with a visualisation tool. See the :doc:`reference/visualise`
documentation. When you visualise your ``PDFDocument``, you'll be able to see each
page of the document in turn, with every ``PDFElement`` highlighted. You can hover
over the elements to see their sections, tags and whether they are ignored or not. This
is very helpful for debugging any problems.

You can use the arrow key icons to change page, and can press home to return to page 1.
You can also use the scroll wheel on your mouse to zoom in and out.

Font Mappings
-------------

You can filter elements by font. The font will be taken from the PDF itself, however
often they have long and confusing names. You can specify a ``font_mapping`` when
you load the document to map these to more memorable names. See the
:doc:`reference/components` reference for the ``PDFDocument`` arguments for more
information.

Tables
------

We have many functions to help extract tables. All of these use the positioning of the
elements on the page to do this. See :doc:`reference/tables`.
