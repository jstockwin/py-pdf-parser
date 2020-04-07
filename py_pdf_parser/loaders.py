from typing import Dict, List, NamedTuple, IO, Optional, TYPE_CHECKING

import logging

from pdfminer.high_level import extract_pages
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
        la_params (dict): The layout parameters passed to PDF Miner for analysis. See
            the PDFMiner documentation here:
            https://pdfminersix.readthedocs.io/en/latest/api/composable.html#laparams.
            Note that py_pdf_parser will re-order the elements it receives from PDFMiner
            so options relating to element ordering will have no effect.
        pdf_file_path (str, optional): Passed to `PDFDocument`. See the documentation
            for `PDFDocument`.
        kwargs: Passed to `PDFDocument`. See the documentation for `PDFDocument`.

    Returns:
        PDFDocument: A PDFDocument with the file loaded.
    """
    if la_params is None:
        la_params = {}

    pages: Dict[int, Page] = {}
    for page in extract_pages(pdf_file, laparams=LAParams(**la_params)):
        elements = [element for element in page if isinstance(element, LTTextContainer)]
        if not elements:
            logger.warning(
                f"No elements detected on page {page.pageid}, skipping this page."
            )
            continue

        pages[page.pageid] = Page(
            width=page.width, height=page.height, elements=elements
        )

    return PDFDocument(pages=pages, pdf_file_path=pdf_file_path, **kwargs)
