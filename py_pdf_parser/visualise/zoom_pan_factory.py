from typing import Callable


class ZoomPanFactory(object):
    """
    Allow matplotlib to zoom (from scrolling) and pan.

    Based on https://stackoverflow.com/a/19829987
    """

    def __init__(self, ax):
        self.ax = ax

        self.press = None
        self.current_xlim = None
        self.current_ylim = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.x_press = None
        self.y_press = None

    def zoom_factory(self, zoom_multiplier) -> Callable:
        """
        Create zoom handlers.

        zoom_multiplier is the multiple we zoom in/out of for each scroll.
        """

        def zoom(event):
            current_xlim = self.ax.get_xlim()
            current_ylim = self.ax.get_ylim()

            x = event.xdata
            y = event.ydata

            # don't crash if you scroll outside the main chart area
            if x is None or y is None:
                return

            # deal with zoom in
            if event.button == "down":
                scale_factor = 1.0 / zoom_multiplier

            # deal with zoom out
            elif event.button == "up":
                scale_factor = zoom_multiplier

            # otherwise
            else:
                scale_factor = 1
                print(event.button)

            new_width = (current_xlim[1] - current_xlim[0]) * scale_factor
            new_height = (current_ylim[1] - current_ylim[0]) * scale_factor

            rel_x = (current_xlim[1] - x) / (current_xlim[1] - current_xlim[0])
            rel_y = (current_ylim[1] - y) / (current_ylim[1] - current_ylim[0])

            new_xlim = [x - new_width * (1 - rel_x), x + new_width * rel_x]
            new_ylim = [y - new_height * (1 - rel_y), y + new_height * rel_y]

            self.ax.set_xlim(new_xlim)
            self.ax.set_ylim(new_ylim)

            self.ax.figure.canvas.draw()

        # get the figure of interest
        fig = self.ax.get_figure()
        fig.canvas.mpl_connect("scroll_event", zoom)

        return zoom

    def pan_factory(self) -> Callable:
        def press(event):
            if event.inaxes != self.ax:
                return

            self.current_xlim = self.ax.get_xlim()
            self.current_ylim = self.ax.get_ylim()
            self.press = self.x0, self.y0, event.xdata, event.ydata
            self.x0, self.y0, self.x_press, self.y_press = self.press

        def release(event):
            self.press = None
            self.ax.figure.canvas.draw()

        def motion(event):
            if self.press is None:
                return
            if event.inaxes != self.ax:
                return

            dx = event.xdata - self.x_press
            dy = event.ydata - self.y_press

            new_xlim = self.current_xlim - dx
            new_ylim = self.current_ylim - dy

            self.current_xlim = new_xlim
            self.current_ylim = new_ylim

            self.ax.set_xlim(self.current_xlim)
            self.ax.set_ylim(self.current_ylim)

            self.ax.figure.canvas.draw()

        fig = self.ax.get_figure()

        # attach the callbacks
        fig.canvas.mpl_connect("button_press_event", press)
        fig.canvas.mpl_connect("button_release_event", release)
        fig.canvas.mpl_connect("motion_notify_event", motion)

        return motion
