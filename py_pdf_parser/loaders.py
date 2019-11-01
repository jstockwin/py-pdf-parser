from typing import Dict, List, IO, Optional

from pdfminer import converter, pdfdocument, pdfinterp, pdfpage, pdfparser
from pdfminer.layout import LTTextContainer, LAParams

from .components import PDFDocument, PDFElement, PageInfo


def load_file(path_to_file: str) -> PDFDocument:
    with open(path_to_file, "rb") as in_file:
        return load(in_file, pdf_file_path=path_to_file)


def load(pdf_file: IO, pdf_file_path: Optional[str] = None) -> PDFDocument:
    parser = pdfparser.PDFParser(pdf_file)
    document = pdfdocument.PDFDocument(parser)

    if not document.is_extractable:
        raise pdfpage.PDFTextExtractionNotAllowed

    resource_manager = pdfinterp.PDFResourceManager()
    device = converter.PDFPageAggregator(
        resource_manager, laparams=LAParams()
    )  # TODO laparams
    interpreter = pdfinterp.PDFPageInterpreter(resource_manager, device)

    elements: List[PDFElement] = []
    page_info: Dict[int, PageInfo] = {}
    for page in pdfpage.PDFPage.create_pages(document):
        interpreter.process_page(page)
        results = device.get_result()

        page_number = results.pageid

        new_elements = [
            PDFElement(element=element, page_number=results.pageid)
            for element in results
            if isinstance(element, LTTextContainer)
        ]

        page_info[page_number] = PageInfo(
            width=results.width,
            height=results.height,
            start_index=len(elements),
            end_index=len(elements) + len(new_elements) - 1,
        )

        elements += new_elements

    return PDFDocument(
        elements=elements, page_info=page_info, pdf_file_path=pdf_file_path
    )
