"""
Marking Scheme PDF Parser
=========================
Ein OOP-basiertes Tool zum Extrahieren von Fragen, Lösungen und Bildern
aus Pearson Edexcel Marking Scheme PDFs.

Autor: Claude
Datum: 2026-02-16
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pdfplumber
from pypdf import PdfReader
import subprocess
import json
import re
from PIL import Image as PILImage


@dataclass
class Mark:
    """Repräsentiert eine einzelne Mark (z.B. M1, A1, B1)"""
    mark_type: str  # M, A, B
    points: int
    ao: str  # Assessment Objective (z.B. "1.1b", "2.1")
    
    def __str__(self):
        return f"{self.mark_type}{self.points}"


@dataclass
class QuestionPart:
    """Repräsentiert einen Teil einer Frage (z.B. 1(a), 2(b)(ii))"""
    part_id: str  # z.B. "1(a)", "2(b)(ii)"
    scheme: str  # Der Lösungstext
    marks: List[Mark] = field(default_factory=list)
    total_marks: Optional[int] = None
    notes: Optional[str] = None
    images: List['ExtractedImage'] = field(default_factory=list)
    
    def add_mark(self, mark: Mark):
        """Fügt eine Mark hinzu"""
        self.marks.append(mark)
    
    def add_image(self, image: 'ExtractedImage'):
        """Fügt ein Bild hinzu"""
        self.images.append(image)


@dataclass
class Question:
    """Repräsentiert eine vollständige Frage mit allen Teilen"""
    question_number: int
    parts: List[QuestionPart] = field(default_factory=list)
    total_marks: Optional[int] = None
    
    def add_part(self, part: QuestionPart):
        """Fügt einen Fragenteil hinzu"""
        self.parts.append(part)
    
    def get_all_images(self) -> List['ExtractedImage']:
        """Gibt alle Bilder aus allen Teilen zurück"""
        all_images = []
        for part in self.parts:
            all_images.extend(part.images)
        return all_images


@dataclass
class ExtractedImage:
    """Repräsentiert ein extrahiertes Bild aus dem PDF"""
    image_id: str
    question_part: str
    page_number: int
    bbox: Optional[Tuple[float, float, float, float]] = None  # (x0, y0, x1, y1)
    image_path: Optional[Path] = None
    image_data: Optional[bytes] = None
    
    def save(self, output_dir: Path):
        """Speichert das Bild in einem Verzeichnis"""
        if self.image_data:
            output_dir.mkdir(parents=True, exist_ok=True)
            filepath = output_dir / f"{self.image_id}.png"
            with open(filepath, 'wb') as f:
                f.write(self.image_data)
            self.image_path = filepath
            return filepath
        return None


@dataclass
class MarkingScheme:
    """Container für ein vollständiges Marking Scheme PDF"""
    pdf_path: Path
    title: str
    exam_board: str  # z.B. "Pearson Edexcel"
    subject: str  # z.B. "Further Mathematics"
    paper_code: str  # z.B. "8FM0_22"
    exam_date: str  # z.B. "Summer 2018"
    questions: List[Question] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def add_question(self, question: Question):
        """Fügt eine Frage hinzu"""
        self.questions.append(question)
    
    def get_question(self, number: int) -> Optional[Question]:
        """Gibt eine spezifische Frage zurück"""
        for q in self.questions:
            if q.question_number == number:
                return q
        return None
    
    def to_json(self, filepath: Path):
        """Exportiert das Marking Scheme als JSON"""
        data = {
            'title': self.title,
            'exam_board': self.exam_board,
            'subject': self.subject,
            'paper_code': self.paper_code,
            'exam_date': self.exam_date,
            'metadata': self.metadata,
            'questions': []
        }
        
        for question in self.questions:
            q_data = {
                'question_number': question.question_number,
                'total_marks': question.total_marks,
                'parts': []
            }
            
            for part in question.parts:
                part_data = {
                    'part_id': part.part_id,
                    'scheme': part.scheme,
                    'marks': [{'type': m.mark_type, 'points': m.points, 'ao': m.ao} 
                              for m in part.marks],
                    'total_marks': part.total_marks,
                    'notes': part.notes,
                    'images': [{'id': img.image_id, 'path': str(img.image_path)} 
                               for img in part.images if img.image_path]
                }
                q_data['parts'].append(part_data)
            
            data['questions'].append(q_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class MarkingSchemeParser:
    """
    Hauptklasse zum Parsen von Marking Scheme PDFs
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")
        
        self.marking_scheme = None
        self.current_question = None
        
    def parse(self) -> MarkingScheme:
        """Parst das gesamte PDF und gibt ein MarkingScheme Objekt zurück"""
        print(f"Parse PDF: {self.pdf_path.name}")
        
        # 1. Extrahiere Metadaten
        metadata = self._extract_metadata()
        
        # 2. Erstelle MarkingScheme Objekt
        self.marking_scheme = MarkingScheme(
            pdf_path=self.pdf_path,
            title=metadata.get('title', ''),
            exam_board=metadata.get('exam_board', ''),
            subject=metadata.get('subject', ''),
            paper_code=metadata.get('paper_code', ''),
            exam_date=metadata.get('exam_date', ''),
            metadata=metadata
        )
        
        # 3. Extrahiere Fragen und Tabellen
        self._extract_questions()
        
        # 4. Extrahiere Bilder
        self._extract_images()
        
        return self.marking_scheme
    
    def _extract_metadata(self) -> Dict:
        """Extrahiert Metadaten aus den ersten Seiten"""
        metadata = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            # Erste Seite enthält typischerweise den Titel
            if len(pdf.pages) > 0:
                first_page_text = pdf.pages[0].extract_text()
                
                # Beispiel-Parsing (anpassbar an deine spezifischen PDFs)
                if "Mark Scheme" in first_page_text:
                    metadata['title'] = 'Mark Scheme (Results)'
                
                # Exam Board
                if "Pearson" in first_page_text or "Edexcel" in first_page_text:
                    metadata['exam_board'] = 'Pearson Edexcel'
                
                # Datum
                date_match = re.search(r'(Summer|Winter)\s+(\d{4})', first_page_text)
                if date_match:
                    metadata['exam_date'] = f"{date_match.group(1)} {date_match.group(2)}"
                
                # Paper Code
                code_match = re.search(r'Paper\s+(\w+_\d+)', first_page_text)
                if code_match:
                    metadata['paper_code'] = code_match.group(1)
                
                # Subject
                if "Further Mathematics" in first_page_text:
                    metadata['subject'] = 'Further Mathematics'
                elif "Mathematics" in first_page_text:
                    metadata['subject'] = 'Mathematics'
        
        return metadata
    
    def _extract_questions(self):
        """Extrahiert alle Fragen aus den Tabellen"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Überspringe Metadaten-Seiten (typischerweise erste 4 Seiten)
                if page_num <= 4:
                    continue
                
                # Extrahiere Tabellen von dieser Seite
                tables = page.extract_tables()
                
                for table in tables:
                    if table:
                        self._process_table(table, page_num)
                
                # Extrahiere auch "Notes" Abschnitte
                text = page.extract_text()
                if text and "Notes" in text:
                    self._extract_notes(text, page_num)
    
    def _process_table(self, table: List[List[str]], page_num: int):
        """Verarbeitet eine einzelne Tabelle"""
        if not table or len(table) < 2:
            return
        
        # Header prüfen
        header = table[0]
        if not self._is_question_table_header(header):
            return
        
        # Verarbeite jede Zeile
        for row in table[1:]:
            if not row or len(row) < 3:
                continue
            
            # Parse Question ID (z.B. "1(a)", "2(b)(ii)")
            question_id = row[0].strip() if row[0] else ""
            if not question_id:
                continue
            
            # Scheme Text
            scheme = row[1].strip() if len(row) > 1 and row[1] else ""
            
            # Marks (z.B. "M1", "A1", "(3)")
            marks_text = row[2].strip() if len(row) > 2 and row[2] else ""
            
            # AOs (Assessment Objectives)
            ao_text = row[3].strip() if len(row) > 3 and row[3] else ""
            
            # Erstelle oder finde die Frage
            q_num = self._extract_question_number(question_id)
            question = self.marking_scheme.get_question(q_num)
            
            if question is None:
                question = Question(question_number=q_num)
                self.marking_scheme.add_question(question)
            
            # Erstelle QuestionPart
            part = QuestionPart(
                part_id=question_id,
                scheme=scheme
            )
            
            # Parse Marks
            marks = self._parse_marks(marks_text, ao_text)
            for mark in marks:
                part.add_mark(mark)
            
            # Parse total marks (z.B. "(3)")
            total = self._extract_total_marks(marks_text)
            if total:
                part.total_marks = total
            
            question.add_part(part)
    
    def _is_question_table_header(self, header: List[str]) -> bool:
        """Prüft ob eine Tabellenzeile ein Question-Table Header ist"""
        if not header or len(header) < 3:
            return False
        
        # Typische Header: ["Question", "Scheme", "Marks", "AOs"]
        header_str = " ".join([cell.lower() if cell else "" for cell in header])
        return "question" in header_str or "scheme" in header_str
    
    def _extract_question_number(self, question_id: str) -> int:
        """Extrahiert die Fragennummer aus einer ID wie '1(a)' oder '2(b)(ii)'"""
        match = re.match(r'(\d+)', question_id)
        if match:
            return int(match.group(1))
        return 0
    
    def _parse_marks(self, marks_text: str, ao_text: str) -> List[Mark]:
        """Parst Mark-Strings wie 'M1', 'A1', 'B1ft'"""
        marks = []
        
        # Pattern für Marks: M1, A1, B1, B1ft, etc.
        pattern = r'([MAB])(\d+)(?:ft)?'
        matches = re.findall(pattern, marks_text)
        
        for mark_type, points in matches:
            mark = Mark(
                mark_type=mark_type,
                points=int(points),
                ao=ao_text
            )
            marks.append(mark)
        
        return marks
    
    def _extract_total_marks(self, marks_text: str) -> Optional[int]:
        """Extrahiert total marks aus einem String wie '(3)' oder '(5 marks)'"""
        match = re.search(r'\((\d+)\)', marks_text)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_notes(self, text: str, page_num: int):
        """Extrahiert Notes-Abschnitte und ordnet sie den Fragen zu"""
        # Finde den Notes-Abschnitt
        notes_match = re.search(r'Notes\s+(.*?)(?=\n\n|\Z)', text, re.DOTALL)
        if notes_match:
            notes_text = notes_match.group(1).strip()
            
            # Versuche, die Frage zu identifizieren
            # (z.B. "(a)" oder "Question 1")
            question_match = re.search(r'\(([a-z]+)\)', notes_text)
            if question_match and self.marking_scheme.questions:
                # Füge Notes zum letzten QuestionPart hinzu
                last_question = self.marking_scheme.questions[-1]
                if last_question.parts:
                    last_question.parts[-1].notes = notes_text
    
    def _extract_images(self):
        """Extrahiert alle Bilder aus dem PDF"""
        print("Extrahiere Bilder...")
        
        # Methode 1: pdfplumber für Inline-Bilder
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Überspringe Metadaten-Seiten
                if page_num <= 4:
                    continue
                
                # Extrahiere Bilder mit pdfplumber
                for img_obj in page.images:
                    try:
                        # Erstelle ExtractedImage
                        img = ExtractedImage(
                            image_id=f"page{page_num}_img{len(page.images)}",
                            question_part="",  # Wird später zugeordnet
                            page_number=page_num,
                            bbox=(img_obj['x0'], img_obj['top'], 
                                  img_obj['x1'], img_obj['bottom'])
                        )
                        
                        # Versuche, die Frage zuzuordnen
                        question = self._find_question_for_page(page_num)
                        if question and question.parts:
                            question.parts[-1].add_image(img)
                    
                    except Exception as e:
                        print(f"Warnung: Bild auf Seite {page_num} konnte nicht extrahiert werden: {e}")
        
        # Methode 2: pdfimages für alle Bilder
        self._extract_images_with_pdfimages()
    
    def _extract_images_with_pdfimages(self):
        """Nutzt pdfimages CLI tool für vollständige Bildextraktion"""
        try:
            # Temporäres Verzeichnis für Bilder
            temp_dir = Path("/home/claude/temp_images")
            temp_dir.mkdir(exist_ok=True)
            
            # pdfimages ausführen
            output_prefix = temp_dir / f"{self.pdf_path.stem}_img"
            subprocess.run([
                "pdfimages",
                "-j",  # JPEG Ausgabe
                "-png",  # PNG Ausgabe
                str(self.pdf_path),
                str(output_prefix)
            ], check=True, capture_output=True)
            
            print(f"Bilder extrahiert nach: {temp_dir}")
            
            # Ordne extrahierte Bilder den Fragen zu
            for img_file in temp_dir.glob("*.png"):
                # Lade Bilddaten
                with open(img_file, 'rb') as f:
                    img_data = f.read()
                
                # Erstelle ExtractedImage
                img = ExtractedImage(
                    image_id=img_file.stem,
                    question_part="",
                    page_number=0,  # Wird bestimmt durch Dateinamen
                    image_data=img_data
                )
                
                # TODO: Intelligentere Zuordnung zu Fragen
                
        except subprocess.CalledProcessError as e:
            print(f"Warnung: pdfimages fehlgeschlagen: {e}")
        except FileNotFoundError:
            print("Warnung: pdfimages nicht installiert. Installiere mit: apt-get install poppler-utils")
    
    def _find_question_for_page(self, page_num: int) -> Optional[Question]:
        """Findet die Frage, die auf einer bestimmten Seite ist"""
        # Einfache Heuristik: Nimm die letzte Frage
        if self.marking_scheme.questions:
            return self.marking_scheme.questions[-1]
        return None
    
    def export_to_json(self, output_path: str):
        """Exportiert das geparste Marking Scheme als JSON"""
        if not self.marking_scheme:
            raise ValueError("Erst parse() aufrufen!")
        
        output_file = Path(output_path)
        self.marking_scheme.to_json(output_file)
        print(f"JSON exportiert nach: {output_file}")
    
    def export_images(self, output_dir: str):
        """Exportiert alle Bilder in ein Verzeichnis"""
        if not self.marking_scheme:
            raise ValueError("Erst parse() aufrufen!")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        image_count = 0
        for question in self.marking_scheme.questions:
            for image in question.get_all_images():
                if image.save(output_path):
                    image_count += 1
        
        print(f"{image_count} Bilder exportiert nach: {output_path}")


# Beispiel-Nutzung
if __name__ == "__main__":
    # Parser erstellen
    parser = MarkingSchemeParser("/mnt/user-data/uploads/markscheme1.pdf")
    
    # PDF parsen
    marking_scheme = parser.parse()
    
    # JSON Export
    parser.export_to_json("/home/claude/markscheme1.json")
    
    # Bilder exportieren
    parser.export_images("/home/claude/images")
    
    # Statistiken ausgeben
    print(f"\n=== Zusammenfassung ===")
    print(f"Titel: {marking_scheme.title}")
    print(f"Exam: {marking_scheme.exam_date}")
    print(f"Paper Code: {marking_scheme.paper_code}")
    print(f"Anzahl Fragen: {len(marking_scheme.questions)}")
    
    for question in marking_scheme.questions:
        print(f"\nFrage {question.question_number}:")
        print(f"  Teile: {len(question.parts)}")
        print(f"  Bilder: {len(question.get_all_images())}")
