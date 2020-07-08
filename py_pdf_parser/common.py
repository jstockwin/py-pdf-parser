from py_pdf_parser.exceptions import InvalidCoordinatesError


class BoundingBox:
    """
    A rectangle, stored using the coordinates (x0, y0) of the bottom left corner, and
    the coordinates (x1, y1) of the top right corner.

    Args:
        x0 (int): The x coordinate of the bottom left corner.
        x1 (int): The x coordinate of the top right corner.
        y0 (int): The y coordinate of the bottom left corner.
        y1 (int): The y coordinate of the top right corner.

    Raises:
        InvalidCoordinatesError: if x1 is smaller than x0 or y1 is smaller than y0.

    Attributes:
        x0 (int): The x coordinate of the bottom left corner.
        x1 (int): The x coordinate of the top right corner.
        y0 (int): The y coordinate of the bottom left corner.
        y1 (int): The y coordinate of the top right corner.
        width (int): The width of the box, equal to x1 - x0.
        height (int): The height of the box, equal to y1 - y0.
    """

    def __init__(self, x0: float, x1: float, y0: float, y1: float):
        if x1 < x0:
            raise InvalidCoordinatesError(
                f"Invalid coordinates, x1 is smaller than x0 ({x1}<{x0})"
            )
        if y1 < y0:
            raise InvalidCoordinatesError(
                f"Invalid coordinates, y1 is smaller than y0 ({y1}<{y0})"
            )
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.width = x1 - x0
        self.height = y1 - y0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BoundingBox):
            raise NotImplementedError(f"Can't compare BoundingBox with {type(other)}")

        return all(
            [
                self.x0 == other.x0,
                self.x1 == other.x1,
                self.y0 == other.y0,
                self.y1 == other.y1,
            ]
        )

    def __repr__(self):
        return f"<BoundingBox x0={self.x0}, x1={self.x1}, y0={self.y0}, y1={self.y1}>"
