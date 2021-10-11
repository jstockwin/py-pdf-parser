from typing import Dict, Tuple, Optional, Callable, TYPE_CHECKING

import logging

import matplotlib
import tkinter as tk
from matplotlib.figure import Figure

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import MouseButton

from py_pdf_parser.components import PDFDocument
from .background import get_pdf_background
from .info_figure import get_clicked_element_info
from .sections import SectionVisualiser

if TYPE_CHECKING:
    from py_pdf_parser.filtering import ElementList
    from py_pdf_parser.components import PDFElement
    from matplotlib.figure import Text
    from matplotlib.axes import Axes
    from matplotlib.backend_bases import MouseEvent

logger = logging.getLogger("PDFParser")


STYLES = {
    "untagged": {"color": "#00a9f4", "linewidth": 1, "alpha": 0.5},
    "tagged": {"color": "#007ac1", "linewidth": 1, "alpha": 0.5},
    "ignored": {"color": "#67daff", "linewidth": 1, "alpha": 0.2, "linestyle": ":"},
}

DPI = 100


class CustomToolbar(NavigationToolbar2Tk):
    def __init__(
        self,
        canvas: tk.Canvas,
        window: tk.Tk,
        first_page_callback: Callable,
        previous_page_callback: Callable,
        next_page_callback: Callable,
        last_page_callback: Callable,
        *args,
        **kwargs,
    ):
        self.first_page_callback = first_page_callback
        self.previous_page_callback = previous_page_callback
        self.next_page_callback = next_page_callback
        self.last_page_callback = last_page_callback
        self.toolitems += (
            (None, None, None, None),  # Divider
            ("First page", "Go to fist page", "back", "first_page_callback"),
            ("Previous page", "Go to previous page", "back", "previous_page_callback"),
            ("Next page", "Go to next page", "forward", "next_page_callback"),
            ("Last page", "Go to last page", "forward", "last_page_callback"),
        )
        super().__init__(canvas, window, *args, **kwargs)

    def reset(self, not_first_page, not_last_page):
        map = {True: tk.ACTIVE, False: tk.DISABLED}
        self._buttons["First page"]["state"] = map[not_first_page]
        self._buttons["Previous page"]["state"] = map[not_first_page]
        self._buttons["Next page"]["state"] = map[not_last_page]
        self._buttons["Last page"]["state"] = map[not_last_page]


class PDFVisualiser:
    """
    Class used to handle visualising the PDF. Do not instantiate this yourself, instead
    you should call the `visualise` function.

    We need a class as we have to keep track of the current page etc.
    """

    document: PDFDocument
    current_page: int
    __ax: "Axes"
    __fig: "Figure"
    __info_fig: Optional["Figure"] = None
    __info_text: Optional["Text"] = None
    __section_visualiser: "SectionVisualiser"

    __clicked_elements: Dict[MouseButton, "PDFElement"] = {}

    def __init__(
        self,
        root: tk.Tk,
        document: PDFDocument,
        current_page: int = 1,
        elements: Optional["ElementList"] = None,
        show_info: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        if not document._pdf_file_path:
            logger.warning(
                "PDFDocument does not initialised with pdf_file_path and so we cannot "
                "add the PDF background for visualisation. Please use load_file "
                "instead of load, or specify pdf_file_path manually"
            )

        self.document = document
        self.current_page = current_page
        if elements is not None:
            self.elements = elements
        else:
            self.elements = document.elements
        self.show_info = show_info

        self.root = root
        if width is None:
            width = self.root.winfo_screenwidth()
        if height is None:
            height = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}")
        title = "py-pdf-parser"
        if self.document._pdf_file_path:
            title += f" - {self.document._pdf_file_path}"
        self.root.title(title)

        self.__fig = Figure(figsize=(5, 4), dpi=DPI)
        self.canvas = FigureCanvasTkAgg(self.__fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.toolbar = CustomToolbar(
            self.canvas,
            self.root,
            next_page_callback=self.__next_page,
            first_page_callback=self.__first_page,
            previous_page_callback=self.__previous_page,
            last_page_callback=self.__last_page,
        )

        self.__ax = self.canvas.figure.add_subplot(111)

        self.__section_visualiser = SectionVisualiser(self.document, self.__ax)

        if self.show_info:
            self.__info_fig, self.__info_text = self.__initialise_info_fig()

        self.__plot_current_page()

    def __plot_current_page(self):
        if self.show_info:
            self.__clear_clicked_elements()

        self.__ax.cla()

        # draw PDF image as background
        page = self.document.get_page(self.current_page)
        if self.document._pdf_file_path is not None:
            background = get_pdf_background(
                self.document._pdf_file_path, self.current_page
            )
            self.__ax.imshow(
                background,
                origin="lower",
                extent=[0, page.width, 0, page.height],
                interpolation="kaiser",
            )
        else:
            self.__ax.set_aspect("equal")
            self.__ax.set_xlim([0, page.width])
            self.__ax.set_ylim([0, page.height])

        page = self.document.get_page(self.current_page)
        for element in page.elements & self.elements:
            style = STYLES["tagged"] if element.tags else STYLES["untagged"]
            self.__plot_element(element, style)

        # We'd like to draw greyed out rectangles around the ignored elements, but these
        # are excluded from ElementLists, so we need to do this manually.
        page_indexes = set(
            range(page.start_element._index, page.end_element._index + 1)
        )
        ignored_indexes_on_page = page_indexes & self.document._ignored_indexes
        for index in ignored_indexes_on_page:
            element = self.document._element_list[index]
            self.__plot_element(element, STYLES["ignored"])

        self.__section_visualiser.plot_sections_for_page(page)

        self.__ax.format_coord = self.__get_annotations
        self.__reset_toolbar()

    def __initialise_info_fig(self) -> Tuple["Figure", "Axes"]:
        window = tk.Toplevel(self.root)

        info_fig = Figure()
        canvas = FigureCanvasTkAgg(info_fig, window)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas.mpl_connect("button_press_event", self.__on_click)

        info_text = info_fig.text(
            0.01,
            0.5,
            "",
            horizontalalignment="left",
            verticalalignment="center",
        )
        return info_fig, info_text

    def __on_click(self, event: "MouseEvent"):
        if event.button == MouseButton.MIDDLE:
            self.__clear_clicked_elements()
            return
        if event.button not in [MouseButton.LEFT, MouseButton.RIGHT]:
            return
        for rect in self.__ax.patches:
            if not rect.contains(event)[0]:
                continue
            # rect is the rectangle we clicked on!
            self.__clicked_elements[event.button] = rect.element
            self.__update_text()

            return

    def __clear_clicked_elements(self):
        self.__clicked_elements = {}
        self.__update_text()

    def __update_text(self):
        self.__info_text.set_text(get_clicked_element_info(self.__clicked_elements))
        self.__info_fig.canvas.draw()

    def __plot_element(self, element: "PDFElement", style: Dict):
        rect = _ElementRectangle(element, **style)
        self.__ax.add_patch(rect)

    def __reset_toolbar(self):
        not_first_page = self.current_page != 1
        not_last_page = self.current_page != self.document.number_of_pages
        self.toolbar.reset(not_first_page, not_last_page)

    def __get_annotations(self, x: float, y: float) -> str:
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

    def __first_page(self):
        self.__set_page(min(self.document.page_numbers))

    def __last_page(self):
        self.__set_page(max(self.document.page_numbers))

    def __next_page(self):
        current_page_idx = self.document.page_numbers.index(self.current_page)
        next_page_idx = min(current_page_idx + 1, self.document.number_of_pages)
        next_page = self.document.page_numbers[next_page_idx]
        self.__set_page(next_page)

    def __previous_page(self):
        current_page_idx = self.document.page_numbers.index(self.current_page)
        previous_page_idx = max(current_page_idx - 1, 0)
        previous_page = self.document.page_numbers[previous_page_idx]
        self.__set_page(previous_page)

    def __set_page(self, page_number: int):
        if self.current_page != page_number:
            self.current_page = page_number
            self.__plot_current_page()
            self.__fig.canvas.draw()


class _ElementRectangle(matplotlib.patches.Rectangle):
    """
    This is essentially the same as a matplotlib.patches.Rectangle, except
    with an added `element` attribute. It also supplies the coordinates for
    the rectangle from the element's bounding box.
    """

    def __init__(self, element: "PDFElement", **style):
        self.element = element
        bbox = element.bounding_box
        super().__init__((bbox.x0, bbox.y0), bbox.width, bbox.height, **style)


def visualise(
    document: PDFDocument,
    page_number: int = 1,
    elements: Optional["ElementList"] = None,
    show_info: bool = False,
    width: Optional[int] = None,
    height: Optional[int] = None,
):
    """
    Visualises a PDFDocument, allowing you to inspect all the elements.

    Will open a Matplotlib window showing the page_number. You can use the black
    buttons on the right of the toolbar to navigate through pages.

    Warning:
        In order to show you the actual PDF behind the elements, your document
        must be initialised with pdf_file_path, and your PDF must be at the given path.
        If this is not done, the background will be white.

    Args:
        document (PDFDocument): The pdf document to visualise.
        page_number (int): The page to visualise. Note you can change pages using
            the arrow keys in the visualisation window.
        elements (ElementList, optional): Which elements of the document to visualise.
            Defaults to all of the elements in the document.
        show_info (bool): Shows an additional window allowing you to click on
            PDFElements and see details about them. Default: False.
        width: (int, optional): The initial width of the visualisation window.
            Default: Screen width.
        height: (int, optional): The initial height of the visualisation window.
            Default: Screen height.
    """
    root = tk.Tk()
    PDFVisualiser(root, document, page_number, elements, show_info, width, height)
    root.mainloop()
