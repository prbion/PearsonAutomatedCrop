# main.py
import pymupdf
import os
import string 
import pytesseract 
from PIL import Image
# Below are the imports for the classes 
from PDFManager import PDFManager
from TaskExtractor import TaskExtractor
from ImageSnipper import ImageSnipper
from Menu import Menu 
from TaskPipeline import TaskPipeline
from ExcelExporter import ExcelExporter

def main():
    menu      = Menu()
    pdf_manager = PDFManager()
    extractor   = TaskExtractor()
    snipper     = ImageSnipper()
    exporter    = ExcelExporter()                

    processor = TaskPipeline(pdf_manager, extractor, snipper, exporter)  

    pdf_path = r"C:\Dev\src\9fm0-02-que-20230606.pdf"  # update as needed
    processor.run(pdf_path, menu)

    # Save Excel file next to the output folder
    excel_filename = f"{menu.folder_name}_questions.xlsx"
    excel_path     = os.path.join(menu.folder_name, excel_filename)
    exporter.save(excel_path)                    

if __name__ == "__main__":
    main()
