# TaskExtractor.py
import pymupdf
import pytesseract 
from PIL import Image
import re 

class TaskExtractor:
    def __init__(self):
        self.mark_pattern   = r"\(\d+\)"          # (4), (5) etc. for mark allocations
        self.header_pattern = r"(\d+\.)"           # 1. , 2. etc. for question headers
        self.roman_pattern  = r"\(([iv]+)\)"       # (i), (ii), (iii), (iv), (v), (vi)…
        self.letter_pattern = r"\(([a-z])\)"       # single lowercase letter in parens

        # Only i and v are treated as exclusively roman — we never go past viii in practice.
        self._roman_only_chars = set('iv')

        # Letter subtask labels (a), (b) etc. always appear in the left margin.
        # Math variables like (x), (z) in f(z) appear mid-line in expressions.
        # 120 pt ≈ left ~17% of a typical A4 PDF page (595 pt wide).
        self._label_max_x0 = 120

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_roman_only(self, text):
        """Return True if the string consists entirely of roman numeral chars (i, v)."""
        return bool(text) and all(c in self._roman_only_chars for c in text.lower())

    def _is_label_position(self, word_tuple):
        """
        Return True if the word's x0 is in the left margin — i.e. a genuine
        subtask label rather than an inline math variable.
        """
        return word_tuple[0] <= self._label_max_x0

    def _match_letter(self, word_text):
        """
        Return the matched letter if word_text is EXACTLY a letter label like (a),
        otherwise None.  Uses fullmatch so that f(z) or az² never match.
        """
        m = re.fullmatch(self.letter_pattern, word_text)
        return m.group(1).lower() if m else None

    # ------------------------------------------------------------------
    # Core extraction
    # ------------------------------------------------------------------

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
        crops      = []
        start_y    = 0
        right_side = (page.rect.width * 0.85) + 5

        for y_coord in y_coordinates:
            top    = start_y
            bottom = y_coord + 5

            if (bottom - top) > 40:
                rect = pymupdf.Rect(0, top, right_side, bottom)
                crops.append(rect)
                start_y = bottom - 5

        return crops

    # ------------------------------------------------------------------
    # Letter subtask detection
    # (all guarded by fullmatch + roman filter + position check)
    # ------------------------------------------------------------------

    def has_letter_subtasks(self, page, crop_rect):
        """
        Return True if this crop area contains genuine letter subtask labels
        like (a), (b), (c) — exact tokens, left-margin, non-roman.
        """
        words = page.get_text("words")
        for w in words:
            letter = self._match_letter(w[4])           # fullmatch — rejects f(z) etc.
            if letter is None:
                continue
            if self._is_roman_only(letter):
                continue
            if not self._is_label_position(w):
                continue
            word_rect = pymupdf.Rect(w[0], w[1], w[2], w[3])
            if crop_rect.contains(word_rect) or crop_rect.intersects(word_rect):
                return True
        return False

    def find_letter_label_for_crop(self, page, crop_rect):
        """
        Find the actual letter subtask label (a, b, c…) within a crop area.
        Returns the letter string, or None if no genuine label is found.
        """
        words = page.get_text("words")
        for w in words:
            letter = self._match_letter(w[4])
            if letter is None:
                continue
            if self._is_roman_only(letter):
                continue
            if not self._is_label_position(w):
                continue
            word_rect = pymupdf.Rect(w[0], w[1], w[2], w[3])
            if crop_rect.contains(word_rect) or crop_rect.intersects(word_rect):
                return letter
        return None

    def find_letter_coordinates_for_crop(self, page, crop_rect):
        """
        Find all (a), (b), (c)… markers within a crop (roman-first hierarchy).
        Returns list of (letter, y_top, y_bottom) sorted by y.
        """
        coords = []
        words  = page.get_text("words")
        for w in words:
            letter = self._match_letter(w[4])
            if letter is None:
                continue
            if self._is_roman_only(letter):
                continue
            if not self._is_label_position(w):
                continue
            word_rect = pymupdf.Rect(w[0], w[1], w[2], w[3])
            if crop_rect.contains(word_rect) or crop_rect.intersects(word_rect):
                coords.append((letter, w[1], w[3]))
        return sorted(coords, key=lambda x: x[1])

    def calculate_letter_crop_areas(self, letter_coords, parent_crop):
        """Mirror of calculate_roman_crop_areas but for letter sub-parts (roman-first hierarchy)."""
        crops = []
        for i, (letter_text, y_top, y_bottom) in enumerate(letter_coords):
            top    = parent_crop.y0 if i == 0 else y_top - 5
            bottom = (letter_coords[i + 1][1] - 5) if i < len(letter_coords) - 1 else parent_crop.y1

            top    = max(top, parent_crop.y0)
            bottom = min(bottom, parent_crop.y1)

            if (bottom - top) > 20:
                rect = pymupdf.Rect(parent_crop.x0, top, parent_crop.x1 + 5, bottom)
                crops.append((letter_text, rect))
        return crops

    # ------------------------------------------------------------------
    # Roman numeral detection
    # ------------------------------------------------------------------

    def find_roman_label_for_crop(self, page, crop_rect):
        """Find the actual roman numeral label within a crop (roman-first hierarchy)."""
        words = page.get_text("words")
        for w in words:
            match = re.fullmatch(self.roman_pattern, w[4])
            if match:
                word_rect = pymupdf.Rect(w[0], w[1], w[2], w[3])
                if crop_rect.contains(word_rect) or crop_rect.intersects(word_rect):
                    return match.group(1).lower()
        return None

    def find_roman_numeral_coordinates(self, page, crop_rect):
        """Find all (i), (ii), (iii)… within a crop (letter-first hierarchy)."""
        coords = []
        words  = page.get_text("words")
        for w in words:
            match = re.fullmatch(self.roman_pattern, w[4])
            if match:
                word_rect = pymupdf.Rect(w[0], w[1], w[2], w[3])
                if crop_rect.contains(word_rect) or crop_rect.intersects(word_rect):
                    coords.append((match.group(1).lower(), w[1], w[3]))
        return sorted(coords, key=lambda x: x[1])

    def calculate_roman_crop_areas(self, roman_coords, parent_crop, page):
        """Calculate crop areas for roman numeral sub-questions (letter-first hierarchy)."""
        crops      = []
        right_side = parent_crop.x1 + 5

        for i, (roman_text, y_top, y_bottom) in enumerate(roman_coords):
            top    = parent_crop.y0 if i == 0 else y_top - 5
            bottom = (roman_coords[i + 1][1] - 5) if i < len(roman_coords) - 1 else parent_crop.y1

            top    = max(top, parent_crop.y0)
            bottom = min(bottom, parent_crop.y1)

            if (bottom - top) > 20:
                rect = pymupdf.Rect(parent_crop.x0, top, right_side, bottom)
                crops.append((roman_text, rect))

        return crops

    # ------------------------------------------------------------------
    # Hierarchy detection
    # ------------------------------------------------------------------

    def detect_hierarchy(self, page, sub_task_crops):
        """
        Returns 'roman_first' if roman numerals are the parent level (i → a, b),
        or 'letter_first' if letters are the parent level (a → i, ii).

        Compares the y-position of the first roman marker vs the first genuine
        letter marker (exact token, left-margin, non-roman) across all crops.
        """
        first_roman_y  = None
        first_letter_y = None
        words = page.get_text("words")

        for w in words:
            word_rect   = pymupdf.Rect(w[0], w[1], w[2], w[3])
            in_question = any(
                crop.contains(word_rect) or crop.intersects(word_rect)
                for crop in sub_task_crops
            )
            if not in_question:
                continue

            if first_roman_y is None:
                if re.fullmatch(self.roman_pattern, w[4]):
                    first_roman_y = w[1]

            if first_letter_y is None:
                letter = self._match_letter(w[4])
                if letter and not self._is_roman_only(letter) and self._is_label_position(w):
                    first_letter_y = w[1]

            if first_roman_y is not None and first_letter_y is not None:
                break

        if first_roman_y is None and first_letter_y is None:
            return 'letter_first'
        if first_roman_y is None:
            return 'letter_first'
        if first_letter_y is None:
            return 'roman_first'

        return 'roman_first' if first_roman_y < first_letter_y else 'letter_first'
