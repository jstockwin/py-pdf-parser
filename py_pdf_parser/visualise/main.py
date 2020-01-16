from typing import Tuple, TYPE_CHECKING

import logging

import matplotlib

matplotlib.use("Qt5Agg", warn=False)  # noqa
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from py_pdf_parser.components import PDFDocument
from .background import get_pdf_background

if TYPE_CHECKING:
    from py_pdf_parser.filtering import ElementList

logger = logging.getLogger("PDFParser")


STYLES = {
    "untagged": {"color": "#00a9f4", "linewidth": 1, "alpha": 0.5},
    "tagged": {"color": "#007ac1", "linewidth": 1, "alpha": 0.5},
    "ignored": {"color": "#67daff", "linewidth": 1, "alpha": 0.2, "linestyle": ":"},
}


class PDFVisualiser:
    """
    Class used to handle visualising the PDF. Do not instantiate this yourself, instead
    you should call the `visualise` function.

    We need a class as we have to keep track of the current page etc.
    """

    document: PDFDocument
    current_page: int
    _fig: Figure
    _ax: Axes
    __first_page_button = None
    __previous_page_button = None
    __next_page_button = None
    __last_page_button = None

    def __init__(
        self,
        document: PDFDocument,
        current_page: int = 1,
        elements: "ElementList" = None,
    ):
        if not document.pdf_file_path:
            logger.warning(
                "PDFDocument does not have pdf_file_path set and so we cannot "
                "add the PDF background for visualisation. Please use load_file "
                "instead of load, or specify pdf_file_path manually"
            )

        self.document = document
        self.current_page = current_page
        if elements is not None:
            self.elements = elements
        else:
            self.elements = document.elements

        page = document.get_page(current_page)
        self._fig, self._ax = self.__initialise_plot(
            width=page.width, height=page.height
        )

    def visualise(self):
        self.__setup_toolbar()
        self.__plot_current_page()
        plt.show()

    def __plot_current_page(self):
        plt.cla()

        # draw PDF image as background
        page = self.document.get_page(self.current_page)
        if self.document.pdf_file_path is not None:
            background = get_pdf_background(
                self.document.pdf_file_path, self.current_page
            )
            plt.imshow(
                background,
                origin="lower",
                extent=[0, page.width, 0, page.height],
                interpolation="kaiser",
            )
        else:
            self._ax.set_xlim([0, page.width])
            self._ax.set_ylim([0, page.height])

        page = self.document.get_page(self.current_page)
        for element in page.elements:
            style = STYLES["tagged"] if element.tags else STYLES["untagged"]
            self.__plot_element(element, style)

        # We'd like to draw greyed out rectangles around the ignored elements, but these
        # are excluded from ElementLists, so we need to do this manually.
        page_indexes = set(
            range(page.start_element._index, page.end_element._index + 1)
        )
        ignored_indexes_on_page = page_indexes & self.document.ignored_indexes
        for index in ignored_indexes_on_page:
            element = self.document.element_list[index]
            self.__plot_element(element, STYLES["ignored"])

        self._ax.format_coord = self.__get_annotations

        self.__reset_toolbar()

    def __plot_element(self, element, style):
        bbox = element.bounding_box
        rect = matplotlib.patches.Rectangle(
            (bbox.x0, bbox.y0), bbox.width, bbox.height, **style
        )
        self._ax.add_patch(rect)

    def __setup_toolbar(self):
        fig_manager = plt.get_current_fig_manager()
        style = fig_manager.toolbar.style()
        fig_manager.toolbar.addSeparator()

        self.__first_page_button = fig_manager.toolbar.addAction(
            style.standardIcon(style.SP_MediaSkipBackward), "First page"
        )
        self.__first_page_button.triggered.connect(self.__first_page)

        self.__previous_page_button = fig_manager.toolbar.addAction(
            style.standardIcon(style.SP_MediaSeekBackward), "Previous page"
        )
        self.__previous_page_button.triggered.connect(self.__previous_page)

        self.__next_page_button = fig_manager.toolbar.addAction(
            style.standardIcon(style.SP_MediaSeekForward), "Next page"
        )
        self.__next_page_button.triggered.connect(self.__next_page)

        self.__last_page_button = fig_manager.toolbar.addAction(
            style.standardIcon(style.SP_MediaSkipForward), "Last page"
        )
        self.__last_page_button.triggered.connect(self.__last_page)

    def __reset_toolbar(self):
        not_first_page = self.current_page != 1
        not_last_page = self.current_page != self.document.number_of_pages
        self.__first_page_button.setEnabled(not_first_page)
        self.__previous_page_button.setEnabled(not_first_page)
        self.__next_page_button.setEnabled(not_last_page)
        self.__last_page_button.setEnabled(not_last_page)

    def __get_annotations(self, x, y) -> str:
        annotation = f"({x:.2f}, {y:.2f})"
        for element in self.elements.filter_by_page(self.current_page):
            bbox = element.bounding_box
            if bbox.x0 <= x <= bbox.x1 and bbox.y0 <= y <= bbox.y1:
                annotation += f" {element}"
                sections_dict = self.document.sectioning.sections_dict
                section_names = [
                    section_name
                    for section_name, section in sections_dict.items()
                    if element in section
                ]
                if section_names:
                    sections_str = "', '".join(section_names)
                    annotation += f", SECTIONS: '{sections_str}'"

        return annotation

    def __initialise_plot(self, width: int, height: int) -> Tuple[Figure, Axes]:
        return plt.subplots(figsize=(height, width))

    def __first_page(self):
        self.__set_page(1)

    def __last_page(self):
        self.__set_page(self.document.number_of_pages)

    def __next_page(self):
        next_page = min(self.current_page + 1, self.document.number_of_pages)
        self.__set_page(next_page)

    def __previous_page(self):
        previous_page = max(self.current_page - 1, 1)
        self.__set_page(previous_page)

    def __set_page(self, page_number):
        if self.current_page != page_number:
            self.current_page = page_number
            self.__plot_current_page()
            self._fig.canvas.draw()


def visualise(
    document: PDFDocument, page_number: int = 1, elements: "ElementList" = None
):
    """
    Visualises a PDFDocument, allowing you to inspect all the elements.

    Will open a Matplotlib window showing the page_number. You can use the black
    buttons on the right of the toolbar to navigate through pages.

    Warning:
        In order to show you the actual PDF behind the elements, your document
        must have pdf_file_path set, and your PDF must be at the given path. If this is
        not set, the background will be white.

    Args:
        document (PDFDocument): The pdf document to visualise.
        page_number (int): The page to visualise. Note you can change pages using
            the arrow keys in the visualisation window.
        elements (ElementList, optional): Which elements of the document to visualise.
            Defaults to all of the elements in the document.
    """
    visualiser = PDFVisualiser(document, page_number, elements)
    visualiser.visualise()
