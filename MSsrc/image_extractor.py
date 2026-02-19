"""
Image Extractor für Marking Scheme PDFs
========================================
Spezialisiertes Modul zum Extrahieren und Verarbeiten von Bildern
aus Marking Scheme PDFs
"""

from pathlib import Path
from typing import List, Tuple, Optional
import subprocess
from PIL import Image
import pdfplumber
from pdf2image import convert_from_path
import io


class ImageExtractor:
    """
    Fortgeschrittener Image Extractor mit mehreren Methoden:
    1. pdfimages (CLI)
    2. pdfplumber 
    3. pdf2image (für komplette Seiten)
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")
    
    def extract_all_images(self, output_dir: str, method: str = "auto") -> List[Path]:
        """
        Extrahiert alle Bilder aus dem PDF
        
        Args:
            output_dir: Ausgabe-Verzeichnis
            method: "pdfimages", "pdfplumber", "pdf2image" oder "auto"
        
        Returns:
            Liste der gespeicherten Bilddateien
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if method == "auto":
            # Versuche pdfimages, falle zurück auf pdfplumber
            try:
                return self._extract_with_pdfimages(output_path)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("pdfimages nicht verfügbar, verwende pdfplumber...")
                return self._extract_with_pdfplumber(output_path)
        
        elif method == "pdfimages":
            return self._extract_with_pdfimages(output_path)
        
        elif method == "pdfplumber":
            return self._extract_with_pdfplumber(output_path)
        
        elif method == "pdf2image":
            return self._extract_with_pdf2image(output_path)
        
        else:
            raise ValueError(f"Unbekannte Methode: {method}")
    
    def _extract_with_pdfimages(self, output_dir: Path) -> List[Path]:
        """Extrahiert Bilder mit pdfimages CLI tool"""
        print("Extrahiere Bilder mit pdfimages...")
        
        output_prefix = output_dir / f"{self.pdf_path.stem}"
        
        # pdfimages ausführen (-j für JPEG, -png für PNG)
        subprocess.run([
            "pdfimages",
            "-all",  # Alle Bildformate
            str(self.pdf_path),
            str(output_prefix)
        ], check=True, capture_output=True)
        
        # Finde alle extrahierten Bilder
        image_files = []
        for ext in ['.png', '.jpg', '.jpeg', '.ppm', '.pbm']:
            image_files.extend(output_dir.glob(f"{self.pdf_path.stem}*{ext}"))
        
        # Konvertiere alle zu PNG für Konsistenz
        png_files = []
        for img_file in image_files:
            if img_file.suffix.lower() != '.png':
                png_file = img_file.with_suffix('.png')
                img = Image.open(img_file)
                img.save(png_file)
                img_file.unlink()  # Lösche Original
                png_files.append(png_file)
            else:
                png_files.append(img_file)
        
        print(f"✓ {len(png_files)} Bilder extrahiert")
        return png_files
    
    def _extract_with_pdfplumber(self, output_dir: Path) -> List[Path]:
        """Extrahiert Bilder mit pdfplumber"""
        print("Extrahiere Bilder mit pdfplumber...")
        
        image_files = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extrahiere Bilder von dieser Seite
                images = page.images
                
                for img_idx, img_obj in enumerate(images):
                    try:
                        # Crop das Bild aus der Seite
                        bbox = (
                            img_obj['x0'],
                            img_obj['top'],
                            img_obj['x1'],
                            img_obj['bottom']
                        )
                        
                        # Rendere die Seite als Bild und croppe
                        page_image = page.to_image(resolution=300)
                        cropped = page_image.original.crop(bbox)
                        
                        # Speichere
                        filename = output_dir / f"page{page_num:03d}_img{img_idx:03d}.png"
                        cropped.save(filename, "PNG")
                        image_files.append(filename)
                    
                    except Exception as e:
                        print(f"Warnung: Konnte Bild {img_idx} auf Seite {page_num} nicht extrahieren: {e}")
        
        print(f"✓ {len(image_files)} Bilder extrahiert")
        return image_files
    
    def _extract_with_pdf2image(self, output_dir: Path) -> List[Path]:
        """Konvertiert jede Seite zu einem Bild"""
        print("Konvertiere PDF-Seiten zu Bildern...")
        
        # Konvertiere PDF zu Bildern
        images = convert_from_path(
            str(self.pdf_path),
            dpi=300,
            fmt='png'
        )
        
        # Speichere jede Seite
        image_files = []
        for i, image in enumerate(images, 1):
            filename = output_dir / f"page{i:03d}.png"
            image.save(filename, "PNG")
            image_files.append(filename)
        
        print(f"✓ {len(image_files)} Seiten konvertiert")
        return image_files
    
    def extract_images_from_page(
        self, 
        page_num: int, 
        output_dir: str,
        crop_margin: int = 10
    ) -> List[Path]:
        """
        Extrahiert alle Bilder von einer spezifischen Seite
        
        Args:
            page_num: Seitennummer (1-basiert)
            output_dir: Ausgabe-Verzeichnis
            crop_margin: Zusätzlicher Rand um das Bild in Pixeln
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        image_files = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            if page_num < 1 or page_num > len(pdf.pages):
                raise ValueError(f"Ungültige Seitennummer: {page_num}")
            
            page = pdf.pages[page_num - 1]
            images = page.images
            
            for img_idx, img_obj in enumerate(images):
                try:
                    # Berechne Bounding Box mit Margin
                    x0 = max(0, img_obj['x0'] - crop_margin)
                    y0 = max(0, img_obj['top'] - crop_margin)
                    x1 = min(page.width, img_obj['x1'] + crop_margin)
                    y1 = min(page.height, img_obj['bottom'] + crop_margin)
                    
                    bbox = (x0, y0, x1, y1)
                    
                    # Rendere und croppe
                    page_image = page.to_image(resolution=300)
                    cropped = page_image.original.crop(bbox)
                    
                    # Speichere
                    filename = output_path / f"page{page_num:03d}_img{img_idx:03d}.png"
                    cropped.save(filename, "PNG")
                    image_files.append(filename)
                    
                    print(f"✓ Extrahiert: {filename.name} ({cropped.width}x{cropped.height}px)")
                
                except Exception as e:
                    print(f"✗ Fehler bei Bild {img_idx} auf Seite {page_num}: {e}")
        
        return image_files
    
    def detect_diagrams_on_page(self, page_num: int) -> List[Tuple[float, float, float, float]]:
        """
        Erkennt Diagramme/Grafiken auf einer Seite basierend auf Linien
        
        Returns:
            Liste von Bounding Boxes (x0, y0, x1, y1)
        """
        bboxes = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            if page_num < 1 or page_num > len(pdf.pages):
                return bboxes
            
            page = pdf.pages[page_num - 1]
            
            # Finde Rechtecke und Linien (typisch für Diagramme)
            rects = page.rects
            lines = page.lines
            
            # Gruppiere nahe beieinander liegende Linien
            # (vereinfachte Heuristik)
            if len(lines) > 4:
                # Berechne Bounding Box um alle Linien
                x_coords = []
                y_coords = []
                
                for line in lines:
                    x_coords.extend([line['x0'], line['x1']])
                    y_coords.extend([line['top'], line['bottom']])
                
                if x_coords and y_coords:
                    bbox = (
                        min(x_coords),
                        min(y_coords),
                        max(x_coords),
                        max(y_coords)
                    )
                    bboxes.append(bbox)
        
        return bboxes
    
    def crop_region(
        self, 
        page_num: int, 
        bbox: Tuple[float, float, float, float],
        output_file: str,
        resolution: int = 300
    ) -> Path:
        """
        Croppt eine spezifische Region aus einer Seite
        
        Args:
            page_num: Seitennummer (1-basiert)
            bbox: Bounding Box (x0, y0, x1, y1)
            output_file: Ausgabe-Datei
            resolution: DPI für das Rendering
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with pdfplumber.open(self.pdf_path) as pdf:
            page = pdf.pages[page_num - 1]
            
            # Rendere Seite
            page_image = page.to_image(resolution=resolution)
            
            # Skaliere bbox entsprechend der Auflösung
            scale = resolution / 72  # 72 DPI ist Standard
            scaled_bbox = tuple(coord * scale for coord in bbox)
            
            # Croppe
            cropped = page_image.original.crop(scaled_bbox)
            
            # Speichere
            cropped.save(output_path, "PNG")
            
            print(f"✓ Region gespeichert: {output_path.name} ({cropped.width}x{cropped.height}px)")
            
            return output_path
    
    def get_image_metadata(self) -> dict:
        """Gibt Metadaten über Bilder im PDF zurück"""
        metadata = {
            'total_pages': 0,
            'pages_with_images': 0,
            'total_images': 0,
            'images_per_page': {}
        }
        
        with pdfplumber.open(self.pdf_path) as pdf:
            metadata['total_pages'] = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, 1):
                num_images = len(page.images)
                if num_images > 0:
                    metadata['pages_with_images'] += 1
                    metadata['total_images'] += num_images
                    metadata['images_per_page'][page_num] = num_images
        
        return metadata


# Hilfsfunktionen
def batch_extract_images(pdf_files: List[str], output_base_dir: str):
    """Extrahiert Bilder aus mehreren PDFs"""
    base_path = Path(output_base_dir)
    
    for pdf_file in pdf_files:
        pdf_path = Path(pdf_file)
        print(f"\n{'='*60}")
        print(f"Verarbeite: {pdf_path.name}")
        print(f"{'='*60}")
        
        # Erstelle Unterverzeichnis für dieses PDF
        output_dir = base_path / pdf_path.stem
        
        # Extrahiere
        extractor = ImageExtractor(pdf_file)
        images = extractor.extract_all_images(str(output_dir))
        
        # Metadaten
        metadata = extractor.get_image_metadata()
        print(f"\nMetadaten:")
        print(f"  Seiten gesamt: {metadata['total_pages']}")
        print(f"  Seiten mit Bildern: {metadata['pages_with_images']}")
        print(f"  Bilder gesamt: {metadata['total_images']}")
        print(f"  Extrahierte Dateien: {len(images)}")


# Beispiel-Nutzung
if __name__ == "__main__":
    # Beispiel 1: Extrahiere alle Bilder aus einem PDF
    extractor = ImageExtractor("/mnt/user-data/uploads/markscheme1.pdf")
    
    # Metadaten anzeigen
    metadata = extractor.get_image_metadata()
    print("Metadaten:")
    print(f"  Seiten: {metadata['total_pages']}")
    print(f"  Bilder: {metadata['total_images']}")
    print(f"  Seiten mit Bildern: {list(metadata['images_per_page'].keys())}")
    
    # Alle Bilder extrahieren
    images = extractor.extract_all_images("/home/claude/extracted_images")
    print(f"\n{len(images)} Bilder extrahiert nach /home/claude/extracted_images/")
    
    # Beispiel 2: Extrahiere Bilder von einer spezifischen Seite
    if metadata['images_per_page']:
        page_with_images = list(metadata['images_per_page'].keys())[0]
        print(f"\nExtrahiere Bilder von Seite {page_with_images}...")
        page_images = extractor.extract_images_from_page(
            page_with_images,
            "/home/claude/page_images"
        )
