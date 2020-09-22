.. _simple-memo:

Simple Memo
-----------

Our first example will be extracting information from a simple memo.

You can :download:`download the example memo here </example_files/simple_memo.pdf>`.

We will assume that your company issues these memos always in a consistent format, i.e. with the "TO", "FROM", "DATE", and "SUBJECT" fields, the main content of the memo. We would like to write some code such that we can extract the information from each memo.

Step 1 - Load the file
......................

First, we should load the file into a :class:`~py_pdf_parser.components.PDFDocument`, using :func:`~py_pdf_parser.loaders.load_file`:

.. code-block:: python

   from py_pdf_parser.loaders import load_file

   document = load_file("simple_memo.pdf")

To check the PDF loaded as expected, we can use the :func:`~py_pdf_parser.visualise.main.visualise` tool by running

.. code-block:: python

   from py_pdf_parser.visualise import visualise

   visualise(document)

This will open a matplotlib window which should look something like the following image:

.. image:: /screenshots/simple_memo_example/visualise.png
   :height: 300px

Py-pdf-parser has extracted each element from the PDF as a :class:`~py_pdf_parser.components.PDFElement`, and is showing a blue box around each element. This is what we are looking for. Always check the visualise tool, since sometimes you will need to adjust the layout parameters so that the tool correctly identifies your elements. We will get on to this in later examples.

Step 2 - Extract reference elements
...................................

Certain elements should be present in every memo. We will use these as reference elements to identify the elements which contain the information we are interested in. We already have our ``document``, which is a :class:`~py_pdf_parser.components.PDFDocument`. We can do :meth:`document.elements <py_pdf_parser.components.PDFDocument.elements>` to get a list (an :class:`~py_pdf_parser.filtering.ElementList`) of all the :class:`~py_pdf_parser.components.PDFElement` in the document, and also to allow us to filter the elements.

The simplest way to extract the elements we are interested in is by text. There are many other options available to us, and a full list can be found on the :ref:`filtering reference page<filtering-reference>`.

We will extract the "TO:", "FROM:", "DATE:" and "SUBJECT:" elements as reference elements, i.e. the elements on the left of the below image. We will then search to the right of each of them in turn, to extract the values for each field.

.. image:: /screenshots/simple_memo_example/top.png
   :height: 200px

To extract the element which says "TO:", we can simply run :meth:`document.elements.filter_by_text_equal("TO:") <py_pdf_parser.filtering.ElementList.filter_by_text_equal>`. This returns a new :class:`~py_pdf_parser.filtering.ElementList` which contains all the elements in the document with text equal to "TO:". In this case, there should only be one element in the list. We could just use ``[0]`` on the element list to access the element in question, however, there is a convenience function, :func:`~py_pdf_parser.filtering.ElementList.extract_single_element` on the :class:`~py_pdf_parser.filtering.ElementList` class to handle this case. This essentially checks if the list has a single element and returns the element for you, otherwise it raises an exception. Use of this is encouraged to make your code more robust and to make any errors more explicit.

.. code-block:: python

   to_element = document.elements.filter_by_text_equal("TO:").extract_single_element()
   from_element = document.elements.filter_by_text_equal("FROM:").extract_single_element()
   date_element = document.elements.filter_by_text_equal("DATE:").extract_single_element()
   subject_element = document.elements.filter_by_text_equal(
       "SUBJECT:"
   ).extract_single_element()

Each of the above elements will be a :class:`~py_pdf_parser.components.PDFElement`.

Step 3 - Extract the data
.........................

In the above section we have extracted our reference elements. We can now use these to do some more filtering to extract the data we want. In particular, we can use :func:`~py_pdf_parser.filtering.ElementList.to_the_right_of`, which will extract elements directly to the right of a given element. It effectively draws a dotted line from the top and bottom of your element out to the right hand side of the page, and any elements which are partially within the box created by the dotted line will be returned. To extract the text from a :class:`~py_pdf_parser.components.PDFElement`, we must also call :func:`.text() <py_pdf_parser.components.PDFElement.text>`.

.. code-block:: python

   to_text = document.elements.to_the_right_of(to_element).extract_single_element().text()
   from_text = (
       document.elements.to_the_right_of(from_element).extract_single_element().text()
   )
   date_text = (
       document.elements.to_the_right_of(date_element).extract_single_element().text()
   )
   subject_text_element = document.elements.to_the_right_of(
       subject_element
   ).extract_single_element()
   subject_text = subject_text_element.text()

Note we keep a reference to the subject text element. This is because we will use it later.

We have now extracted the data from the top of the memo, for example ``to_text`` will be ``"All Developers"``. The code does not rely on who the memo is to, and so it should still work for a memo with different values.

The last thing we need to do is extract the content of the memo. In our example there is only one paragraph, and so only one element, but if there were multiple paragraphs there could be multiple elements. There are a few ways to do this. It is probably the case that all the content elements are below the "SUBJECT:" element, however if the text started too far to the right this may not be the case. Instead, we can just use :func:`~py_pdf_parser.filtering.ElementList.after` to filter for elements strictly after the ``subject_text_element``:

.. code-block:: python

   content_elements = document.elements.after(subject_element)
   content_text = "\n".join(element.text() for element in content_elements)

That is now everything extracted from the memo. We can wrap our output into any data structure we fancy, for example json:

.. code-block:: python

   output = {
       "to": to_text,
       "from": from_text,
       "date": date_text,
       "subject": subject_text,
       "content": content_text,
   }

Full Code
.........

Here is the full script constructed above:

.. code-block:: python

   from py_pdf_parser.loaders import load_file

   # Step 1 - Load the document
   document = load_file("simple_memo.pdf")

   # We could visualise it here to check it looks correct:
   # from py_pdf_parser.visualise import visualise
   # visualise(document)

   # Step 2 - Extract reference elements:
   to_element = document.elements.filter_by_text_equal("TO:").extract_single_element()
   from_element = document.elements.filter_by_text_equal("FROM:").extract_single_element()
   date_element = document.elements.filter_by_text_equal("DATE:").extract_single_element()
   subject_element = document.elements.filter_by_text_equal(
       "SUBJECT:"
   ).extract_single_element()

   # Step 3 - Extract the data
   to_text = document.elements.to_the_right_of(to_element).extract_single_element().text()
   from_text = (
       document.elements.to_the_right_of(from_element).extract_single_element().text()
   )
   date_text = (
       document.elements.to_the_right_of(date_element).extract_single_element().text()
   )
   subject_text_element = document.elements.to_the_right_of(
       subject_element
   ).extract_single_element()
   subject_text = subject_text_element.text()

   content_elements = document.elements.after(subject_element)
   content_text = "\n".join(element.text() for element in content_elements)

   output = {
       "to": to_text,
       "from": from_text,
       "date": date_text,
       "subject": subject_text,
       "content": content_text,
   }

This gives:
::

   >>> from pprint import pprint
   >>> pprint(output)

   {'content': 'A new PDF Parsing tool\n'
               'There is a new PDF parsing tool available, called py-pdf-parser - '
               'you should all check it out!\n'
               'I think it could really help you extract that data we need from '
               'those PDFs.',
    'date': '1st January 2020',
    'from': 'John Smith',
    'subject': 'A new PDF Parsing tool',
    'to': 'All Developers'}
