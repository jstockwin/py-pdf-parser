from typing import Dict, List, NamedTuple, IO, Optional, TYPE_CHECKING

import logging

from pdfminer import converter, pdfdocument, pdfinterp, pdfpage, pdfparser
from pdfminer.layout import LTTextContainer, LAParams

from .components import PDFDocument

if TYPE_CHECKING:
    from pdfminer.layout import LTComponent

logger = logging.getLogger("PDFParser")


class Page(NamedTuple):
    """
    This is used to pass PDF Miner elements of a page when instantiating PDFDocument.

    Args:
        width (int): The width of the page.
        height (int): The height of the page.
        elements (list): A list of PDF Miner elements (LTComponents) on the page.
    """

    width: int
    height: int
    elements: List["LTComponent"]


def load_file(
    path_to_file: str, la_params: Optional[Dict] = None, **kwargs
) -> PDFDocument:
    """
    Loads a file according to the specified file path.

    All other arguments are passed to `load`, see the documentation for `load`.

    Returns:
        PDFDocument: A PDFDocument with the specified file loaded.
    """
    with open(path_to_file, "rb") as in_file:
        return load(in_file, pdf_file_path=path_to_file, la_params=la_params, **kwargs)


def load(
    pdf_file: IO,
    pdf_file_path: Optional[str] = None,
    la_params: Optional[Dict] = None,
    **kwargs,
) -> PDFDocument:
    """
    Loads the pdf file into a PDFDocument.

    Args:
        pdf_file (io): The PDF file.
        la_params (dict): The layout parameters passed to PDF Miner for analysis. These
            are not obviously documented by PDF Miner, but we give our understanding
            (which is taken from
            https://github.com/obeattie/pdfminer/wiki/pdfminer.layout)
            below. Note the numerical values are specified as a proportion of the length
            of each character in question.
            `direction`: 'V' denotes vertical text direction, anything else denotes
            horizontal. Default: None.
            `line_overlap`: The amount lines can overlap. Default 0.5.
            `char_margin`: Characters whose distance is closer than this are grouped
            into one word. Default 1.0.
            `line_margin`: Two lines whose distance is closer than the value here are
            grouped as a text box. Default 0.5.
            `word_margin`: Two words whose distance is closer than this value are
            grouped as a text box. Default 0.1.
        pdf_file_path (str, optional): Passed to `PDFDocument`. See the documentation
            for `PDFDocument`.
        kwargs: Passed to `PDFDocument`. See the documentation for `PDFDocument`.

    Returns:
        PDFDocument: A PDFDocument with the file loaded.

    Raises:
        pdfminer.pdfpage.PDFTextExtractionNotAllowed: If the document does not allow
            text extraction.
    """
    if la_params is None:
        la_params = {}

    parser = pdfparser.PDFParser(pdf_file)
    document = pdfdocument.PDFDocument(parser)

    if not document.is_extractable:
        raise pdfpage.PDFTextExtractionNotAllowed

    resource_manager = pdfinterp.PDFResourceManager()
    device = converter.PDFPageAggregator(
        resource_manager, laparams=LAParams(**la_params)
    )
    interpreter = pdfinterp.PDFPageInterpreter(resource_manager, device)

    pages: Dict[int, Page] = {}
    for page in pdfpage.PDFPage.create_pages(document):
        interpreter.process_page(page)
        results = device.get_result()

        page_number = results.pageid

        elements = [
            element for element in results if isinstance(element, LTTextContainer)
        ]

        if not elements:
            logger.warning(
                f"No elements detected on page {page_number}, skipping this page."
            )
            continue

        pages[page_number] = Page(
            width=results.width, height=results.height, elements=elements
        )

    return PDFDocument(pages=pages, pdf_file_path=pdf_file_path, **kwargs)
