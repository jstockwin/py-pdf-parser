import os

from py_pdf_parser.loaders import load_file

from tests.base import BaseTestCase


class TestSimpleMemo(BaseTestCase):
    def test_output_is_correct(self):
        # The code below should match that in the documentation example "simple_memo"
        # Step 1 - Load the document
        file_path = os.path.join(
            os.path.dirname(__file__),
            "../../docs/source/example_files/simple_memo.pdf",
        )
        document = load_file(file_path)

        # We could visualise it here to check it looks correct:
        # from py_pdf_parser.visualise import visualise
        # visualise(document)

        # Step 2 - Extract reference elements:
        to_element = document.elements.filter_by_text_equal(
            "TO:"
        ).extract_single_element()
        from_element = document.elements.filter_by_text_equal(
            "FROM:"
        ).extract_single_element()
        date_element = document.elements.filter_by_text_equal(
            "DATE:"
        ).extract_single_element()
        subject_element = document.elements.filter_by_text_equal(
            "SUBJECT:"
        ).extract_single_element()

        # Step 3 - Extract the data
        to_text = (
            document.elements.to_the_right_of(to_element)
            .extract_single_element()
            .text()
        )
        from_text = (
            document.elements.to_the_right_of(from_element)
            .extract_single_element()
            .text()
        )
        date_text = (
            document.elements.to_the_right_of(date_element)
            .extract_single_element()
            .text()
        )
        subject_text_element = document.elements.to_the_right_of(
            subject_element
        ).extract_single_element()
        subject_text = subject_text_element.text()

        content_elements = document.elements.after(subject_element)
        content_text = "\n".join(element.text() for element in content_elements)

        output = {
            "to": to_text,
            "from": from_text,
            "date": date_text,
            "subject": subject_text,
            "content": content_text,
        }

        self.assertDictEqual(
            output,
            {
                "content": (
                    "A new PDF Parsing tool\n"
                    "There is a new PDF parsing tool available, called py-pdf-parser - "
                    "you should all check it out!\n"
                    "I think it could really help you extract that data we need from "
                    "those PDFs."
                ),
                "date": "1st January 2020",
                "from": "John Smith",
                "subject": "A new PDF Parsing tool",
                "to": "All Developers",
            },
        )
