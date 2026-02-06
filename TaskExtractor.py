# TaskExtractor.py
import pymupdf
import pytesseract 
from PIL import Image
import re 

class TaskExtractor:
    def __init__(self):
        # Muster für die Punktzahlen am Rand, z.B. (3)
        self.regex_pattern = r"\(\d+\)"

    def find_coordinates(self, page):
        """Findet alle Y-Koordinaten der Punkt-Markierungen."""
        y_coordinates = []
        words = page.get_text("words") 
        for w in words:
            if re.search(self.regex_pattern, w[4]):
                # w[1] ist oben, w[3] ist unten am Wort
                y_coordinates.append(w[1])
                y_coordinates.append(w[3])
        return sorted(y_coordinates)

    def calculate_crop_areas(self, y_coordinates, page):
        """Erstellt eine Liste von Bildbereichen für jede Teilaufgabe."""
        if len(y_coordinates) < 2:
            return []

        crops = []
        # Wir starten beim ersten gefundenen Text (oder ganz oben)
        start_y = 0 
        
        # Wir gehen durch die Koordinaten-Paare
        # Da jedes Wort ein y0 und y1 hat, springen wir in 2er Schritten
        for i in range(1, len(y_coordinates), 2):
            top = start_y
            bottom = y_coordinates[i] + 10 # 10px Puffer nach unten
            
            # Breite begrenzen (schneidet den grauen Balken rechts ab)
            right_side = page.rect.width * 0.85
            
            rect = pymupdf.Rect(0, top, right_side, bottom)
            crops.append(rect)
            
            # Der nächste Ausschnitt beginnt dort, wo dieser endete
            start_y = bottom - 5 # Kleiner Überlapp, damit nichts fehlt
            
        return crops
