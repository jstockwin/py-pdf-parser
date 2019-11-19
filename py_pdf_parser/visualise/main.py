from typing import Tuple, TYPE_CHECKING

import matplotlib

matplotlib.use("Qt5Agg", warn=False)  # noqa
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from py_pdf_parser.components import PDFDocument
from .zoom_pan_factory import ZoomPanFactory
from .background import get_pdf_background

if TYPE_CHECKING:
    from py_pdf_parser.filtering import ElementList


STYLES = {
    "untagged": {"color": "#00a9f4", "linewidth": 1, "alpha": 0.5},
    "tagged": {"color": "#007ac1", "linewidth": 1, "alpha": 0.5},
    "ignored": {"color": "#67daff", "linewidth": 1, "alpha": 0.2, "linestyle": ":"},
}


class PDFVisualiser:
    document: PDFDocument
    current_page: int
    _fig: Figure
    _ax: Axes

    def __init__(
        self,
        document: PDFDocument,
        current_page: int = 1,
        elements: "ElementList" = None,
    ):
        if not document.pdf_file_path:
            raise Exception(
                "Can only visualise when there is a file path.. sorry"
            )  # TODO

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
        self.__plot_current_page()

        # setup toolbar
        fig_manager = plt.get_current_fig_manager()
        fig_manager.toolbar.actions()[0].triggered.connect(self.__page_home)
        fig_manager.toolbar.actions()[1].triggered.connect(self.__previous_page)
        fig_manager.toolbar.actions()[2].triggered.connect(self.__next_page)

        # zoom/pan handling
        zoom_pan_handler = ZoomPanFactory(self._ax)
        zoom_pan_handler.zoom_factory(zoom_multiplier=1.1)
        zoom_pan_handler.pan_factory()

        plt.show()

    def __plot_current_page(self):
        plt.cla()

        # draw PDF image as background
        page = self.document.get_page(self.current_page)
        background = get_pdf_background(self.document.pdf_file_path, self.current_page)
        plt.imshow(
            background,
            origin="lower",
            extent=[0, page.width, 0, page.height],
            interpolation="kaiser",
        )

        for element in self.elements.filter_by_page(self.current_page):
            style = STYLES["untagged"]
            if element.ignore:
                style = STYLES["ignored"]
            elif element.tags:
                style = STYLES["tagged"]
            bbox = element.bounding_box
            rect = matplotlib.patches.Rectangle(
                (bbox.x0, bbox.y0), bbox.width, bbox.height, **style
            )

            # Draw rectangle
            self._ax.add_patch(rect)

        self._ax.format_coord = self.__get_annotations

    def __get_annotations(self, x, y):
        annotation = f"({x:.2f}, {y:.2f})"
        for element in self.elements.filter_by_page(self.current_page):
            bbox = element.bounding_box
            if bbox.x0 <= x <= bbox.x1 and bbox.y0 <= y <= bbox.y1:
                annotation += f" ELEMENT[FONT: {element.font}"
                if element.tags:
                    tags_str = "', '".join(element.tags)
                    annotation += f", TAGS: '{tags_str}'"
                sections_dict = self.document.sectioning.sections_dict
                section_names = [
                    section_name
                    for section_name, section in sections_dict.items()
                    if element in section
                ]
                if section_names:
                    sections_str = "', '".join(section_names)
                    annotation += f", SECTIONS: '{sections_str}'"
                annotation += "]"

        return annotation

    def __initialise_plot(self, width: int, height: int) -> Tuple[Figure, Axes]:
        return plt.subplots(figsize=(height, width))

    def __page_home(self):
        if self.current_page != 1:
            self.current_page = 1
            self.__plot_current_page()

    def __next_page(self):
        if self.current_page < self.document.number_of_pages:
            self.current_page += 1
            self.__plot_current_page()

    def __previous_page(self):
        if self.current_page > 1:
            self.current_page += -1
            self.__plot_current_page()


def visualise(
    document: PDFDocument, page_number: int = 1, elements: "ElementList" = None
):
    visualiser = PDFVisualiser(document, page_number, elements)
    visualiser.visualise()
