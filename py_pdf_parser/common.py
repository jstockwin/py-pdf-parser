class BoundingBox:
    def __init__(self, x0, x1, y0, y1):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.width = x1 - x0
        self.height = y1 - y0
