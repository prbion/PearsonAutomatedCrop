from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pdfplumber
from PIL import Image
import re


class QuestionTableCrop:
    """Repräsentiert einen Crop einer Fragen-Tabelle"""
    
    def __init__(
        self,
        question_id: str,
        bbox: Tuple[float, float, float, float],
        page_num: int
    ):
        self.question_id = question_id
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.page_num = page_num
        self.image: Optional[Image.Image] = None
        self.output_path: Optional[Path] = None
    
    def __repr__(self):
        return f"QuestionTableCrop(Q{self.question_id}, page={self.page_num})"


class QuestionCropper:
    """
    Croppt komplette Fragen-Tabellen aus Marking Scheme PDFs.
    
    Features:
    - Erkennt Tabellen-Struktur automatisch
    - Gruppiert Zeilen nach Question Number
    - Croppt komplette Frage mit allen Sub-parts
    - Hohe Auflösung für gute Lesbarkeit
    """
    
    def __init__(self, pdf_path: str, resolution: int = 300):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")
        
        self.resolution = resolution
        self.crops: List[QuestionTableCrop] = []
    
    def extract_all_questions(
        self,
        output_dir: str,
        start_page: int = 5,  # Überspringe Metadaten
        end_page: Optional[int] = None
    ) -> List[Path]:
        """
        Extrahiert alle Fragen als einzelne Tabellen-Crops.
        
        Args:
            output_dir: Ausgabe-Verzeichnis
            start_page: Erste Seite zum Scannen (1-basiert)
            end_page: Letzte Seite (None = bis Ende)
        
        Returns:
            Liste der gespeicherten Crop-Dateien
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"QUESTION CROPPER: {self.pdf_path.name}")
        print(f"{'='*60}\n")
        
        saved_files = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            # Bestimme Seitenbereich
            if end_page is None:
                end_page = len(pdf.pages)
            
            current_question = None
            current_rows = []
            current_bbox = None
            current_page = None
            
            for page_num in range(start_page - 1, min(end_page, len(pdf.pages))):
                page = pdf.pages[page_num]
                print(f"📄 Scanne Seite {page_num + 1}...")
                
                # Extrahiere Tabellen
                tables = page.extract_tables()
                
                for table in tables:
                    if not self._is_question_table(table):
                        continue
                    
                    # Finde die Tabelle in den page.tables (für Bounding Box)
                    table_obj = self._find_table_object(page, table)
                    if not table_obj:
                        continue
                    
                    # Verarbeite jede Zeile der Tabelle
                    for row_idx, row in enumerate(table[1:], 1):  # Skip header
                        if not row or len(row) < 2:
                            continue
                        
                        question_cell = (row[0] or "").strip()
                        
                        # Prüfe ob neue Frage beginnt
                        q_num = self._extract_question_number(question_cell)
                        
                        if q_num is not None:
                            # Speichere vorherige Frage
                            if current_question and current_rows:
                                crop = self._create_crop(
                                    current_question,
                                    current_rows,
                                    current_page,
                                    table_obj
                                )
                                if crop:
                                    saved = self._save_crop(crop, output_path, page)
                                    if saved:
                                        saved_files.append(saved)
                            
                            # Starte neue Frage
                            current_question = question_cell
                            current_rows = [row_idx]
                            current_page = page_num
                        
                        elif current_question:
                            # Füge Zeile zur aktuellen Frage hinzu
                            current_rows.append(row_idx)
            
            # Speichere letzte Frage
            if current_question and current_rows:
                # Hole letzte Seite und Tabelle
                page = pdf.pages[current_page]
                tables = page.extract_tables()
                if tables:
                    table_obj = self._find_table_object(page, tables[0])
                    if table_obj:
                        crop = self._create_crop(
                            current_question,
                            current_rows,
                            current_page,
                            table_obj
                        )
                        if crop:
                            saved = self._save_crop(crop, output_path, page)
                            if saved:
                                saved_files.append(saved)
        
        print(f"\n✅ {len(saved_files)} Fragen erfolgreich gecroppt")
        return saved_files
    
    def _is_question_table(self, table: List[List[str]]) -> bool:
        """Prüft ob eine Tabelle eine Fragen-Tabelle ist"""
        if not table or len(table) < 2:
            return False
        
        header = table[0]
        if not header or len(header) < 3:
            return False
        
        # Prüfe auf typische Header
        header_str = " ".join([str(cell).lower() for cell in header if cell])
        return "question" in header_str and "scheme" in header_str
    
    def _find_table_object(self, page, table_data):
        """Findet das Table-Objekt mit Bounding Box"""
        # pdfplumber hat eine tables Property mit Bounding Boxes
        for table_obj in page.find_tables():
            return table_obj  # Nimm erste Tabelle
        return None
    
    def _extract_question_number(self, cell: str) -> Optional[str]:
        """
        Extrahiert Question Number aus Zelle.
        Erkennt: "1(i)", "2(a)", "5(a)", etc.
        """
        if not cell:
            return None
        
        # Pattern für Question IDs
        patterns = [
            r'^(\d+)\s*\([a-z]+\)',  # 1(a), 2(b)
            r'^(\d+)$',  # Nur Nummer
        ]
        
        for pattern in patterns:
            match = re.match(pattern, cell.strip())
            if match:
                return cell.strip()
        
        return None
    
    def _create_crop(
        self,
        question_id: str,
        row_indices: List[int],
        page_num: int,
        table_obj
    ) -> Optional[QuestionTableCrop]:
        """Erstellt einen Crop für eine Frage"""
        if not row_indices:
            return None
        
        # Berechne Bounding Box
        # Die Tabelle hat eine bbox Property
        table_bbox = table_obj.bbox  # (x0, top, x1, bottom)
        
        # Wir müssen die Zeilen-Höhen berechnen
        # Vereinfachung: Nehme die komplette Tabellen-Höhe
        # (In Zukunft könnten wir die genauen Zeilen-Positionen berechnen)
        
        crop = QuestionTableCrop(
            question_id=question_id,
            bbox=table_bbox,
            page_num=page_num
        )
        
        return crop
    
    def _save_crop(
        self,
        crop: QuestionTableCrop,
        output_dir: Path,
        page
    ) -> Optional[Path]:
        """Speichert einen Crop als PNG"""
        try:
            # Rendere die Seite mit hoher Auflösung
            page_image = page.to_image(resolution=self.resolution)
            
            # Skaliere bbox entsprechend der Auflösung
            scale = self.resolution / 72  # 72 DPI ist Standard
            scaled_bbox = tuple(coord * scale for coord in crop.bbox)
            
            # Croppe
            cropped = page_image.original.crop(scaled_bbox)
            
            # Erstelle Dateinamen
            # "question_1(a).png" -> "question_1a.png"
            safe_name = crop.question_id.replace("(", "").replace(")", "")
            filename = output_dir / f"question_{safe_name}.png"
            
            # Speichere
            cropped.save(filename, "PNG", optimize=True, quality=95)
            
            crop.image = cropped
            crop.output_path = filename
            
            print(f"✓ {filename.name} ({cropped.width}x{cropped.height}px)")
            
            return filename
        
        except Exception as e:
            print(f"✗ Fehler beim Speichern von {crop.question_id}: {e}")
            return None


class ImprovedQuestionCropper(QuestionCropper):
    """
    Verbesserte Version mit präziser Zeilen-Erkennung.
    Croppt exakt die Zeilen einer Frage, nicht die ganze Tabelle.
    """
    
    def extract_all_questions(
        self,
        output_dir: str,
        start_page: int = 5,
        end_page: Optional[int] = None,
        include_header: bool = True,
        margin: int = 5
    ) -> List[Path]:
        """
        Extrahiert Fragen mit präzisen Bounding Boxes.
        
        Args:
            output_dir: Ausgabe-Verzeichnis
            start_page: Erste Seite
            end_page: Letzte Seite
            include_header: Header in jeden Crop einschließen?
            margin: Zusätzlicher Rand in Pixeln
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"IMPROVED QUESTION CROPPER: {self.pdf_path.name}")
        print(f"{'='*60}\n")
        
        saved_files = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            if end_page is None:
                end_page = len(pdf.pages)
            
            # Gruppiere Fragen über Seiten hinweg
            all_questions = {}
            
            for page_num in range(start_page - 1, min(end_page, len(pdf.pages))):
                page = pdf.pages[page_num]
                print(f" Analysing Page {page_num + 1}...")
                
                # Finde Fragen auf dieser Seite
                page_questions = self._extract_questions_from_page(
                    page,
                    page_num,
                    include_header
                )
                
                # Merge mit existierenden Fragen
                for q_id, q_data in page_questions.items():
                    if q_id in all_questions:
                        # Frage geht über mehrere Seiten
                        # Nutze die erweiterte bbox
                        all_questions[q_id]['bbox'] = self._merge_bboxes(
                            all_questions[q_id]['bbox'],
                            q_data['bbox']
                        )
                    else:
                        all_questions[q_id] = q_data
            
            # Erstelle Crops für alle Fragen
            for q_id, q_data in all_questions.items():
                page = pdf.pages[q_data['page_num']]
                
                crop = QuestionTableCrop(
                    question_id=q_id,
                    bbox=q_data['bbox'],
                    page_num=q_data['page_num']
                )
                
                saved = self._save_crop_with_margin(
                    crop,
                    output_path,
                    page,
                    margin
                )
                
                if saved:
                    saved_files.append(saved)
        
        print(f"\n {len(saved_files)} Questions successfully cropped ")
        return saved_files
    
    def _extract_questions_from_page(
        self,
        page,
        page_num: int,
        include_header: bool
    ) -> Dict:
        """Extrahiert alle Fragen von einer Seite mit präzisen Bounding Boxes"""
        questions = {}
        
        # Finde die Tabelle
        tables = page.find_tables()
        if not tables:
            return questions
        
        table = tables[0]  # Nimm erste Tabelle
        table_bbox = table.bbox
        
        # Extrahiere Tabellen-Daten
        table_data = table.extract()
        if not table_data or len(table_data) < 2:
            return questions
        
        # Header-Höhe berechnen
        header_height = 0
        if include_header and table.rows:
            header_row = table.rows[0]
            header_height = header_row.bbox[3] - header_row.bbox[1]
        
        # Gruppiere Zeilen nach Frage
        current_question = None
        question_rows = []
        
        for row_idx, row in enumerate(table.rows):
            # Skip Header
            if row_idx == 0:
                continue
            
            # Extrahiere Daten aus erster Zelle
            row_data = table_data[row_idx] if row_idx < len(table_data) else None
            if not row_data or not row_data[0]:
                # Leere Zeile, füge zu aktueller Frage hinzu
                if current_question:
                    question_rows.append(row)
                continue
            
            question_cell = row_data[0].strip()
            q_num = self._extract_question_number(question_cell)
            
            if q_num:
                # Neue Frage gefunden
                # Speichere vorherige Frage
                if current_question and question_rows:
                    bbox = self._calculate_rows_bbox(
                        question_rows,
                        table_bbox,
                        header_height if include_header else 0
                    )
                    questions[current_question] = {
                        'bbox': bbox,
                        'page_num': page_num,
                        'rows': len(question_rows)
                    }
                
                # Starte neue Frage
                current_question = question_cell
                question_rows = [row]
            
            elif current_question:
                # Füge Zeile zur aktuellen Frage hinzu
                question_rows.append(row)
        
        # Speichere letzte Frage
        if current_question and question_rows:
            bbox = self._calculate_rows_bbox(
                question_rows,
                table_bbox,
                header_height if include_header else 0
            )
            questions[current_question] = {
                'bbox': bbox,
                'page_num': page_num,
                'rows': len(question_rows)
            }
        
        return questions
    
    def _calculate_rows_bbox(
        self,
        rows: List,
        table_bbox: Tuple,
        header_height: float
    ) -> Tuple[float, float, float, float]:
        """Berechnet die Bounding Box für eine Gruppe von Zeilen"""
        if not rows:
            return table_bbox
        
        # x0 und x1 von der Tabelle
        x0 = table_bbox[0]
        x1 = table_bbox[2]
        
        # y0 von der ersten Zeile (minus Header wenn inkludiert)
        first_row_top = rows[0].bbox[1]
        if header_height > 0:
            first_row_top -= header_height
        
        # y1 von der letzten Zeile
        last_row_bottom = rows[-1].bbox[3]
        
        return (x0, first_row_top, x1, last_row_bottom)
    
    def _merge_bboxes(
        self,
        bbox1: Tuple[float, float, float, float],
        bbox2: Tuple[float, float, float, float]
    ) -> Tuple[float, float, float, float]:
        """Merged zwei Bounding Boxes"""
        return (
            min(bbox1[0], bbox2[0]),
            min(bbox1[1], bbox2[1]),
            max(bbox1[2], bbox2[2]),
            max(bbox1[3], bbox2[3])
        )
    
    def _save_crop_with_margin(
        self,
        crop: QuestionTableCrop,
        output_dir: Path,
        page,
        margin: int
    ) -> Optional[Path]:
        """Speichert Crop mit zusätzlichem Rand"""
        try:
            # Rendere Seite
            page_image = page.to_image(resolution=self.resolution)
            
            # Skaliere bbox
            scale = self.resolution / 72
            scaled_bbox = tuple(coord * scale for coord in crop.bbox)
            
            # Füge Margin hinzu
            x0, y0, x1, y1 = scaled_bbox
            margin_scaled = margin * scale
            
            x0 = max(0, x0 - margin_scaled)
            y0 = max(0, y0 - margin_scaled)
            x1 = min(page_image.original.width, x1 + margin_scaled)
            y1 = min(page_image.original.height, y1 + margin_scaled)
            
            final_bbox = (x0, y0, x1, y1)
            
            # Croppe
            cropped = page_image.original.crop(final_bbox)
            
            # Dateiname
            safe_name = crop.question_id.replace("(", "").replace(")", "").replace(" ", "_")
            filename = output_dir / f"question_{safe_name}.png"
            
            # Speichere
            cropped.save(filename, "PNG", optimize=True, quality=95)
            
            print(f"✓ {filename.name} ({cropped.width}x{cropped.height}px)")
            
            return filename
        
        except Exception as e:
            print(f" Fehler: {e}")
            import traceback
            traceback.print_exc()
            return None


# Beispiel-Nutzung
if __name__ == "__main__":
    # Test mit markscheme1.pdf
    cropper = ImprovedQuestionCropper(
        "/mnt/user-data/uploads/markscheme1.pdf",
        resolution=300
    )
    
    crops = cropper.extract_all_questions(
        output_dir="/home/claude/question_crops",
        start_page=5,  # Überspringe Metadaten
        include_header=True,
        margin=10  # 10 Pixel Rand
    )
    
    print(f"\nErfolgreich {len(crops)} Fragen gecroppt!")
    print(f"Gespeichert in: /home/claude/question_crops/")
