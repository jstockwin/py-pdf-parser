.. _extracting-text-from-figures:

Extracting Text From Figures
----------------------------
PDFs are structured documents, and can contain Figures. By default, PDFMiner.six and
hence py-pdf-parser does not extract text from figures.

You can :download:`download an example here </example_files/figure.pdf>`. In the
example, there is figure which contains a red square, and some text. Below the figure
there is some more text.

By default, the text in the figure will not be included:

.. code-block:: python

   from py_pdf_parser.loaders import load_file
   document = load_file("figure.pdf")
   print([element.text() for element in document.elements])

which results in:

::

   ["Here is some text outside of an image"]

To include the text inside the figure, we must pass the ``all_texts`` layout parameter.
This is documented in the PDFMiner.six documentation, `here
<https://pdfminersix.readthedocs.io/en/latest/reference/composable.html#laparams>`_.

The layout parameters can be passed to both :meth:`~py_pdf_parser.loaders.load` and
:meth:`~py-pdf-parser.loaders.load_file` as a dictionary to the ``la_params`` argument.

In our case:

.. code-block:: python

   from py_pdf_parser.loaders import load_file
   document = load_file("figure.pdf", la_params={"all_texts": True})
   print([element.text() for element in document.elements])

which results in:

::

   ["This is some text in an image", "Here is some text outside of an image"]
