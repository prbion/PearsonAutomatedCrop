# main.py
import pymupdf
import string 
import pytesseract 
from PIL import Image
# Below are the imports for the classes 
from PDFManager import PDFManager
from TaskExtractor import TaskExtractor
from ImageSnipper import ImageSnipper
from Menu import Menu 
from TaskPipeline import TaskPipeline

def main():
    # 1. Setup
    menu = Menu()
    
    # 2. Initialize tools
    pdf_manager = PDFManager()
    extractor = TaskExtractor()
    snipper = ImageSnipper()
    
    # 3. Create the coordinator (The Processor)
    processor = TaskPipeline(pdf_manager, extractor, snipper)

    # 4. Execute
    pdf_path = r"C:\Dev\src\9FM0_02_que_20190607.pdf"
    
    # CHANGE: Pass the whole 'menu' object, not just the prefix string
    processor.run(pdf_path, menu)

if __name__ == "__main__":
    main()
