# TaskExtractor.py
import pymupdf
import pytesseract 
from PIL import Image

class TaskExtractor:
    def __init__(self):
        regex_pattern = r"\(\d+\)"  # Regular expression pattern to match "(number)" which is the marks you can get for a question


def find_coordinates(self, page):
    totalCoordinates = 0
    y_coordinates = [totalCoordinates]
    
    text_blocks = page.get_text("blocks")
    for block in text_blocks:
        y_coordinates.append(block[1])  # Append the y-coordinate of each block
        totalCoordinates += 1

        
def calculate_crop_area(y_coordinates):
    if not y_coordinates:
        return 0, 0, 0, 0  # Return default crop area if no coordinates are found


