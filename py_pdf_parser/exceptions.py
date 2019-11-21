class PDFParserError(Exception):
    pass


# Components
class PageNotFoundError(PDFParserError):
    pass


class IndexNotSetError(PDFParserError):
    pass


class PageNumberNotSetError(PDFParserError):
    pass


class NoElementsOnPageError(PDFParserError):
    pass


# Filtering
class NoElementFoundError(PDFParserError):
    pass


class MultipleElementsFoundError(PDFParserError):
    pass


# Tables
class TableExtractionError(PDFParserError):
    pass


class InvalidTableError(PDFParserError):
    pass


class InvalidTableHeaderError(PDFParserError):
    pass
