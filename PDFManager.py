# PDFManager.py
import pymupdf
import pytesseract 
from PIL import Image


class PDFManager:
    def __init__(self):
        self.file_path = ""
        self.doc = None

    def open_file(self, file_path):
        self.file_path = file_path
        self.doc = pymupdf.open(file_path)

    def get_page_count(self):
        return len(self.doc)

    def get_current_page(self, page_number):
        return self.doc[page_number]

    def close_pdf(self):
        if self.doc:
            self.doc.close()
            self.doc = None
