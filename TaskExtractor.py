# TaskExtractor.py
import pymupdf
import pytesseract 
from PIL import Image
import re 

class TaskExtractor:
    def __init__(self):
        self.mark_pattern = r"\(\d+\)"
        self.header_pattern = r"(\d+\.)"

    def find_current_question_name(self, page):
        words = page.get_text("words")
        for w in words:
            if re.search(self.header_pattern, w[4]):
                # Returns "1" instead of "1."
                return w[4].replace(".", "").strip()
        return "Unknown"

    def find_mark_coordinates(self, page):
        y_coordinates = []
        words = page.get_text("words") 
        for w in words:
            if re.search(self.mark_pattern, w[4]):
                y_coordinates.append(w[3]) # Bottom of the mark
        return sorted(y_coordinates)

    def calculate_crop_areas(self, y_coordinates, page):
        crops = []
        start_y = 0 
        right_side = page.rect.width * 0.85 

        for y_coord in y_coordinates:
            top = start_y
            bottom = y_coord + 10  # Slight buffer for safety
            
            # Only save if the crop is big enough to be a real question
            if (bottom - top) > 40:
                rect = pymupdf.Rect(0, top, right_side, bottom)
                crops.append(rect)
                # Next part starts where this one ended
                start_y = bottom - 5 
            
        return crops
