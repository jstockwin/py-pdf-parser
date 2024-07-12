from typing import TYPE_CHECKING, List, Optional, Union

import _tkinter
import logging
import os
import tkinter as tk
from unittest import TestCase

from PIL import Image

if TYPE_CHECKING:
    from pdfminer.layout import LTComponent

    from py_pdf_parser.components import PDFElement
    from py_pdf_parser.filtering import ElementList


# Turn of debug spam from pdfminer, matplotlib, shapely
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("shapely").setLevel(logging.WARNING)


class BaseTestCase(TestCase):
    # Helper functions
    def assert_original_element_in(
        self, original_element: "LTComponent", element_list: "ElementList"
    ):
        pdf_element = self.extract_element_from_list(original_element, element_list)
        self.assertIn(pdf_element, element_list)

    def assert_original_element_list_list_equal(
        self,
        original_element_list_list: List[List[Optional["LTComponent"]]],
        element_list_list: List[List[Optional["PDFElement"]]],
    ):
        self.assertEqual(len(original_element_list_list), len(element_list_list))
        for original_element_list, element_list in zip(
            original_element_list_list, element_list_list
        ):
            self.assert_original_element_list_equal(original_element_list, element_list)

    def assert_original_element_list_equal(
        self,
        original_element_list: List[Optional["LTComponent"]],
        element_list: Union[List[Optional["PDFElement"]], "ElementList"],
    ):
        self.assertEqual(len(original_element_list), len(element_list))
        for original_element, element in zip(original_element_list, element_list):
            if original_element is None or element is None:
                self.assertIsNone(original_element)
                self.assertIsNone(element)
            else:
                self.assert_original_element_equal(original_element, element)

    def assert_original_element_equal(
        self, original_element: "LTComponent", element: "PDFElement"
    ):
        self.assertEqual(original_element, element.original_element)

    def extract_element_from_list(
        self,
        original_element: "LTComponent",
        element_list: Union[List[Optional["PDFElement"]], "ElementList"],
    ) -> "PDFElement":
        return [
            elem
            for elem in element_list
            if elem is not None
            if elem.original_element == original_element
        ][0]


class BaseVisualiseTestCase(BaseTestCase):
    """
    See the answer from ivan_pozdeev at
    https://stackoverflow.com/questions/4083796/how-do-i-run-unittest-on-a-tkinter-app
    for the setUp, tearDown and pump_events methods. This basically allows us to
    run tk.mainloop() manually using pump_events, thus allowing us to use visualise
    without blocking the thread.

    There is also a custom check_images function to do comparison of the screenshots
    from visualise. You can set self.WRITE_NEW_TEST_IMAGES to True to write new images
    if they don't exist. This also allows you to delete images which are old, and then
    run the tests with WRITE_NEW_TEST_IMAGES=True to replace them.
    """

    WRITE_NEW_TEST_IMAGES = False

    def setUp(self):
        self.root = tk.Tk()
        self.pump_events()

    def tearDown(self):
        if self.root:
            self.root.destroy()
            self.pump_events()

    def pump_events(self):
        while self.root.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
            pass

    def check_images(self, visualiser, image_name):
        self.pump_events()
        root_path = os.path.join(os.path.dirname(__file__), "data", "images")
        existing_file_path = os.path.join(root_path, f"{image_name}.png")
        new_file_path = os.path.join(root_path, f"{image_name}-new.png")

        # Check if file exists (write if not)
        if not os.path.isfile(existing_file_path):
            if not self.WRITE_NEW_TEST_IMAGES:
                self.fail(f"Could not find existing image for {image_name=}. Set ")

            visualiser._PDFVisualiser__fig.savefig(existing_file_path)

        # Check images are identical (fail if not)
        existing_image = Image.open(existing_file_path)

        visualiser._PDFVisualiser__fig.savefig(new_file_path)
        new_image = Image.open(new_file_path)

        if new_image.tobytes() != existing_image.tobytes():
            self.fail(f"Images differ for {image_name=}.")

        os.remove(new_file_path)
