# main.py
import pymupdf
import pytesseract 
from PIL import Image
# Below are the imports for the classes 
from PDFManager import PDFManager
from TaskExtractor import TaskExtractor
from ImageSnipper import ImageSnipper


def main():
    
    pdf_manager = PDFManager()
    extractor = TaskExtractor()
    snipper = ImageSnipper()

    pdf_path = r"C:\Dev\src\8fm0-21-que-20240518.pdf"  # put the path to your PDF file here
    pdf_manager.open_file(pdf_path)


    num_pages = pdf_manager.get_page_count()
    
    for i in range(num_pages):
        page = pdf_manager.get_current_page(i)
        coords = extractor.find_coordinates(page)
        
        # Hol dir jetzt alle einzelnen Bereiche
        sub_task_crops = extractor.calculate_crop_areas(coords, page)
        
        for task_index, crop_rect in enumerate(sub_task_crops):
            output_name = f"page_{i+1}_task_{task_index+1}.png"
            snipper.crop_and_save(page, crop_rect, output_name)
            


    pdf_manager.close_pdf()

if __name__ == "__main__":
    main()
