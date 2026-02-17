# TaskExtractor.py
import pymupdf
import pytesseract 
from PIL import Image
import re 

class TaskExtractor:
    def __init__(self):
        self.mark_pattern = r"\(\d+\)" # (4), (5) etc. for marking subtasks
        self.header_pattern = r"(\d+\.)"
        self.roman_pattern = r"\(([ivx]+)\)"       # (i), (ii), (iii), (iv), (v), (vi)...
        self.letter_pattern = r"\(([a-z])\)"        # Single lowercase letter in parens

        # Characters that are ONLY roman numerals (not letter subtasks).
        # We use ivx because exam roman sub-questions go i, ii, iii, iv, v, vi...
        # Importantly we do NOT include l, c, d, m because (d) is a valid letter subtask.
        self._roman_only_chars = set('ivx')

    def find_current_question_name(self, page):
        words = page.get_text("words")
        for w in words:
            if re.search(self.header_pattern, w[4]):
                return w[4].replace(".", "").strip()
        return "Unknown"

    def find_mark_coordinates(self, page):
        y_coordinates = []
        words = page.get_text("words") 
        for w in words:
            if re.search(self.mark_pattern, w[4]):
                y_coordinates.append(w[3])
        return sorted(y_coordinates)

    def calculate_crop_areas(self, y_coordinates, page):
        crops = []
        start_y = 0 
        right_side = (page.rect.width * 0.85) + 5 

        for y_coord in y_coordinates:
            top = start_y 
            bottom = y_coord + 5
            
            if (bottom - top) > 40:
                rect = pymupdf.Rect(0, top, right_side, bottom)
                crops.append(rect)
                start_y = bottom - 5 
            
        return crops

    def _is_roman_only(self, text):
        """Return True if the string consists entirely of roman numeral chars (i, v, x)."""
        return bool(text) and all(c in self._roman_only_chars for c in text.lower())

    def has_letter_subtasks(self, page, crop_rect):
        """Check if this crop area contains letter subtasks like (a), (b), (c).
        
        Crucially, this returns False for roman numeral markers like (i) or (v)
        which would otherwise match the single-lowercase-letter pattern.
        """
        words = page.get_text("words")
        
        for w in words:
            match = re.search(self.letter_pattern, w[4])
            if match:
                letter = match.group(1).lower()
                # Skip if the matched single letter is purely a roman numeral character.
                # e.g. (i) or (v) should not be counted as a letter subtask.
                if self._is_roman_only(letter):
                    continue
                word_rect = pymupdf.Rect(w[0], w[1], w[2], w[3])
                if crop_rect.contains(word_rect) or crop_rect.intersects(word_rect):
                    return True
        return False
    
    def find_roman_numeral_coordinates(self, page, crop_rect):
        """Find (i), (ii), (iii) etc. within a specific crop area."""
        coords = []
        words = page.get_text("words")
        
        for w in words:
            match = re.search(self.roman_pattern, w[4])
            if match:
                word_rect = pymupdf.Rect(w[0], w[1], w[2], w[3])
                if crop_rect.contains(word_rect) or crop_rect.intersects(word_rect):
                    roman_numeral = match.group(1).lower()
                    coords.append((roman_numeral, w[1], w[3]))
        
        return sorted(coords, key=lambda x: x[1])
    
    def calculate_roman_crop_areas(self, roman_coords, parent_crop, page):
        """Calculate crop areas for roman numeral sub-questions.
        
        Each crop:
        - First: starts at parent_crop.y0, ends just before the next marker
        - Middle: starts just before its marker, ends just before the next
        - Last: starts just before its marker, ends at parent_crop.y1
        """
        crops = []
        right_side = parent_crop.x1 + 5
        
        for i, (roman_text, y_top, y_bottom) in enumerate(roman_coords):
            if i == 0:
                top = parent_crop.y0
            else:
                top = y_top - 5
            
            if i < len(roman_coords) - 1:
                next_y_top = roman_coords[i + 1][1]
                bottom = next_y_top - 5
            else:
                bottom = parent_crop.y1
            
            top = max(top, parent_crop.y0)
            bottom = min(bottom, parent_crop.y1)
            
            if (bottom - top) > 20:
                rect = pymupdf.Rect(parent_crop.x0, top, right_side, bottom)
                crops.append((roman_text, rect))
        
        return crops
