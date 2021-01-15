from typing import TYPE_CHECKING, Optional, List, Tuple, Dict

import pyvoronoi
from shapely import geometry, ops
from matplotlib import cm

if TYPE_CHECKING:
    from py_pdf_parser.components import PDFPage, PDFDocument, PDFElement
    from py_pdf_parser.sectioning import Section
    from matplotlib.axes import Axes


# The simple boundary margins are used when trying to draw simple rectangles around
# sections - we see if each of them work in turn. A higher margin means more space
# between the elements and the section boundary line.
SIMPLE_BOUNDARY_MARGINS = [10, 5, 2, 0]


class SectionVisualiser:
    """
    Used internally to draw outlines of sections on the visualise plot.

    We first try to draw a simple rectangle around the section with a fixed margin, for
    increasingly small margins. If this doesn't work (because an element that is not
    in the section would be within the section outline rectangle) then we instead
    construct the boundary as follows:

    We create a Voronoi diagram around all of the elements on the page, and the page
    boundaries (actually we get a diagram around each side of the bounding box of each
    element). Then for each line in the diagram we check if it was generated between one
    box which is in the section and one which isn't, and if so we draw it.

    This produces some slightly interested outlines, and so we also run a simplification
    check. This takes three points on the outline, and if the triangle created by
    joining them together doesn't contain any of our elements, we can remove the middle
    point to make the whole shape a bit simpler.

    It can still produce some slightly interesting shapes, but does work fairly well.
    Importantly, every element in the section will be within the outline, and no boxes
    which are not in the section will be (which cannot always be achieved by simply
    drawing a rectangle around all the points in the section).

    It does add some time when changing page on the visualise tool, but the whole
    process is done in <0.5 sections which is acceptable for a development tool.
    """

    all_elements: List["PDFElement"]
    document: "PDFDocument"
    page: "PDFPage"
    pv: Optional["pyvoronoi.Pyvoronoi"]
    pv_segments: Optional[List]

    __ax: "Axes"
    __sections_by_page_number: Dict[int, List["Section"]]

    def __init__(self, document: "PDFDocument", ax: "Axes"):
        self.document = document
        self.__ax = ax

        colour_map = cm.get_cmap("Dark2").colors
        self.__colour_mapping = {
            section.unique_name: colour_map[idx % len(colour_map)]
            for idx, section in enumerate(self.document.sectioning.sections)
        }

        self.__sections_by_page_number = {}

    def __get_sections_for_page(self, page: "PDFPage") -> List["Section"]:
        if page.page_number not in self.__sections_by_page_number:
            self.__sections_by_page_number[page.page_number] = [
                section
                for section in self.document.sectioning.sections
                if section.elements & page.elements
            ]
        return self.__sections_by_page_number[page.page_number]

    def __get_segment_for_element(self, element: "PDFElement") -> List:
        bbox = element.bounding_box
        return [
            ((bbox.x0, bbox.y0), (bbox.x0, bbox.y1)),
            ((bbox.x0, bbox.y1), (bbox.x1, bbox.y1)),
            ((bbox.x1, bbox.y1), (bbox.x1, bbox.y0)),
            ((bbox.x1, bbox.y0), (bbox.x0, bbox.y0)),
        ]

    def __get_segments_for_elements(self, elements: List["PDFElement"]) -> List:
        return [
            (start, end)
            for element in elements
            for start, end in self.__get_segment_for_element(element)
        ]

    def __get_element_boxes(self, elements: List["PDFElement"]):
        return [
            geometry.box(
                element.bounding_box.x0,
                element.bounding_box.y0,
                element.bounding_box.x1,
                element.bounding_box.y1,
            )
            for element in elements
        ]

    def __simplify_outlines(
        self, line: geometry.LineString
    ) -> Tuple[List[int], List[int]]:
        """
        Simplified the outline by considering set of 3 consecutive vertices, and if
        there are no elements in this triangle, removes the middle vertex from the
        shape. This is done iteratively around the shape until no further changes are
        made.
        """
        xs, ys = line.xy

        # The last point is the same as the first point, which makes things a bit more
        # complicated. We simply remove the last point and add it back at the end.
        xs.pop(-1)
        ys.pop(-1)
        boxes = self.__get_element_boxes(self.all_elements)
        idx = 0
        since_last_changed = 0
        while since_last_changed <= len(xs) + 1:
            idx1 = (idx + 1) % len(xs)
            idx2 = (idx + 2) % len(xs)

            x0 = xs[idx]
            x1 = xs[idx1]
            x2 = xs[idx2]

            y0 = ys[idx]
            y1 = ys[idx1]
            y2 = ys[idx2]

            triangle_points = ((x0, y0), (x1, y1), (x2, y2), (x0, y0))
            triangle = geometry.Polygon(triangle_points)
            if triangle.area < 0.1 or not any(
                triangle.intersects(box) for box in boxes
            ):
                xs.pop(idx1)
                ys.pop(idx1)
                since_last_changed = 0
            else:
                since_last_changed += 1

            idx = (idx + 1) % len(xs)

        # Add the last point back
        xs.append(xs[0])
        ys.append(ys[0])
        return xs, ys

    def __plot_edges(self, to_plot: List, edges: List, vertices: List, label: str):
        lines = []
        for edge_idx in to_plot:
            edge = edges[edge_idx]
            start_vertex = vertices[edge.start]
            end_vertex = vertices[edge.end]
            # Note it could be that the edge is supposed to be parabola (edge.is_linear
            # will be false), but in our case we always have boxes with 90 degree
            # corners. If it's a parabola then the focus is one of these corners, and by
            # drawing a line instead of a parabola we at worse cut through this point,
            # which is fine.
            lines.append(
                geometry.LineString(
                    [[start_vertex.X, start_vertex.Y], [end_vertex.X, end_vertex.Y]]
                )
            )
        merged_line = ops.linemerge(geometry.MultiLineString(lines))
        kwargs = {"label": label, "alpha": 0.5, "color": self.__colour_mapping[label]}
        # Merged line is either a MultiLineString which means we need to draw multiple
        # lines, or it is a LineString which means we only need to draw one.
        if isinstance(merged_line, geometry.MultiLineString):
            for line in merged_line:
                xs, ys = self.__simplify_outlines(line)
                self.__ax.plot(xs, ys, **kwargs)
                kwargs.pop(
                    "label", None
                )  # Only pass label once for single legend entry
        else:
            xs, ys = self.__simplify_outlines(merged_line)
            self.__ax.plot(xs, ys, **kwargs)

    def __plot_section(self, section: "Section"):
        if self.pv is None or self.pv_segments is None:
            self.pv, self.pv_segments = self.__get_voronoi()
        edges = self.pv.GetEdges()
        vertices = self.pv.GetVertices()
        cells = self.pv.GetCells()

        # If an ignored element is within the section, we need to draw lines around it.
        # The following code gets the first and last non-ignored elements in the section
        # on the page, and then gets all elements between (inclusive) these elements,
        # even if they are ignored.
        section_elements_on_page = section.elements & self.page.elements
        section_elements = [
            section.document._element_list[index]
            for index in range(
                section_elements_on_page[0]._index,
                section_elements_on_page[-1]._index + 1,
            )
        ]
        section_segments = self.__get_segments_for_elements(section_elements)
        in_section = [point in section_segments for point in self.pv_segments]

        to_plot = []
        for idx, edge in enumerate(edges):
            first_segment = cells[edge.cell].site
            second_segment = cells[edges[edge.twin].cell].site
            # We should plot if the first segment is in the section and the second isn't
            if in_section[first_segment] and not in_section[second_segment]:
                to_plot.append(idx)

        self.__plot_edges(to_plot, edges, vertices, label=section.unique_name)

    def __get_voronoi(self) -> Tuple[pyvoronoi.Pyvoronoi, List]:
        all_segments = self.__get_segments_for_elements(self.all_elements)
        # Add the page boundary as segments:
        all_segments += [
            [(0, 0), (0, self.page.height)],
            [(0, 0), (self.page.width, 0)],
            [(0, self.page.height), (self.page.width, self.page.height)],
            [(self.page.width, 0), (self.page.width, self.page.height)],
        ]

        pv = pyvoronoi.Pyvoronoi(10)
        for segment in all_segments:
            pv.AddSegment(segment)

        pv.Construct()
        return pv, all_segments

    def __get_boundary_for_elements(
        self, elements: List["PDFElement"], margin: int
    ) -> Tuple[float, float, float, float]:
        x0s = [element.bounding_box.x0 for element in elements]
        x1s = [element.bounding_box.x1 for element in elements]
        y0s = [element.bounding_box.y0 for element in elements]
        y1s = [element.bounding_box.y1 for element in elements]

        x0 = min(x0s) - margin
        x1 = max(x1s) + margin
        y0 = min(y0s) - margin
        y1 = max(y1s) + margin

        return x0, x1, y0, y1

    def __plot_section_simple(self, section) -> bool:
        section_elements_on_page = section.elements & self.page.elements
        non_section_elements = self.page.elements - section_elements_on_page
        boxes = self.__get_element_boxes(non_section_elements)

        for margin in SIMPLE_BOUNDARY_MARGINS:
            x0, x1, y0, y1 = self.__get_boundary_for_elements(
                section_elements_on_page, margin=margin
            )

            boundary = geometry.box(x0, y0, x1, y1)

            if not any(box.intersects(boundary) for box in boxes):
                # No elements outside of the section are within this boundary, and as
                # such we can simply draw this boundary as the section outline. Break.
                break
        else:
            # None of the margins gave us a box which did not contain any non-section
            # elements. We cannot use the simple method.
            return False

        label = section.unique_name

        kwargs = {"label": label, "alpha": 0.5, "color": self.__colour_mapping[label]}
        self.__ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], **kwargs)

        return True

    def plot_sections_for_page(self, page: "PDFPage"):
        self.pv = None
        self.pv_segments = None
        self.page = page

        sections = self.__get_sections_for_page(page)

        if not sections:
            # No sections on page, nothing to plot
            return

        # We want to include ignored elements for this bit.
        page_indexes = set(
            range(page.start_element._index, page.end_element._index + 1)
        )
        ignored_indexes_on_page = page_indexes & self.document._ignored_indexes
        self.all_elements = list(page.elements) + [
            self.document._element_list[index] for index in ignored_indexes_on_page
        ]

        for section in sections:
            plotted = self.__plot_section_simple(section)
            if not plotted:
                self.__plot_section(section)

        # Show the legend
        self.__ax.legend()
