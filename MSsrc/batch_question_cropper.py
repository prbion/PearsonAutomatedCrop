"""
Batch Question Cropper
======================
Verarbeitet alle Marking Scheme PDFs und erstellt Question-Crops.
"""

from question_cropper import ImprovedQuestionCropper
from pathlib import Path
from typing import List
import time


def crop_all_pdfs(
    pdf_files: List[str],
    output_base_dir: str = "/home/claude/all_question_crops",
    resolution: int = 300,
    margin: int = 10,
    start_page: int = 5
):
    """
    Croppt Fragen aus allen PDFs.
    
    Args:
        pdf_files: Liste der PDF-Dateien
        output_base_dir: Basis-Ausgabeverzeichnis
        resolution: DPI für Crops (höher = bessere Qualität)
        margin: Rand um Crops in Pixeln
        start_page: Erste Seite zum Scannen
    """
    base_path = Path(output_base_dir)
    
    all_results = {}
    total_crops = 0
    
    print("="*70)
    print("BATCH QUESTION CROPPER")
    print("="*70)
    print(f"PDFs zu verarbeiten: {len(pdf_files)}")
    print(f"Ausgabe: {output_base_dir}")
    print(f"Resolution: {resolution} DPI")
    print(f"Margin: {margin}px")
    print("="*70)
    
    for pdf_file in pdf_files:
        pdf_path = Path(pdf_file)
        
        if not pdf_path.exists():
            print(f"\n⚠️  SKIP: {pdf_path.name} nicht gefunden")
            continue
        
        print(f"\n{'='*70}")
        print(f"PDF: {pdf_path.name}")
        print(f"{'='*70}")
        
        # Erstelle Unterverzeichnis für dieses PDF
        output_dir = base_path / pdf_path.stem
        
        try:
            start_time = time.time()
            
            # Erstelle Cropper
            cropper = ImprovedQuestionCropper(
                str(pdf_path),
                resolution=resolution
            )
            
            # Extrahiere Fragen
            crops = cropper.extract_all_questions(
                output_dir=str(output_dir),
                start_page=start_page,
                include_header=True,
                margin=margin
            )
            
            elapsed = time.time() - start_time
            
            # Statistiken
            all_results[pdf_path.name] = {
                'crops': len(crops),
                'output_dir': str(output_dir),
                'time': elapsed
            }
            
            total_crops += len(crops)
            
            print(f"\n✅ Fertig in {elapsed:.1f}s")
            print(f"📁 Gespeichert in: {output_dir}")
            
        except Exception as e:
            print(f"\n❌ FEHLER bei {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()
            all_results[pdf_path.name] = {
                'crops': 0,
                'error': str(e)
            }
    
    # Finale Zusammenfassung
    print("\n" + "="*70)
    print("ZUSAMMENFASSUNG")
    print("="*70)
    
    for pdf_name, result in all_results.items():
        if 'error' in result:
            print(f"❌ {pdf_name}: FEHLER - {result['error']}")
        else:
            print(f"✅ {pdf_name}: {result['crops']} Fragen ({result['time']:.1f}s)")
    
    print(f"\nGesamt: {total_crops} Fragen-Crops erstellt")
    print(f"Ausgabe: {output_base_dir}")
    print("="*70)
    
    return all_results


def crop_single_pdf(
    pdf_file: str,
    output_dir: str,
    **kwargs
):
    """Croppt ein einzelnes PDF"""
    cropper = ImprovedQuestionCropper(pdf_file, resolution=kwargs.get('resolution', 300))
    
    return cropper.extract_all_questions(
        output_dir=output_dir,
        start_page=kwargs.get('start_page', 5),
        include_header=kwargs.get('include_header', True),
        margin=kwargs.get('margin', 10)
    )


def compare_crops(results: dict):
    """Vergleicht die Ergebnisse verschiedener PDFs"""
    print("\n" + "="*70)
    print("VERGLEICH")
    print("="*70)
    
    for pdf_name, result in results.items():
        if 'error' not in result:
            avg_size = "N/A"  # Könnte berechnet werden
            print(f"{pdf_name}:")
            print(f"  Fragen: {result['crops']}")
            print(f"  Zeit: {result['time']:.1f}s")
            print(f"  Durchschnitt: {result['time']/max(result['crops'], 1):.2f}s/Frage")


# Beispiel-Nutzung
if __name__ == "__main__":
    # Alle 3 PDFs
    pdf_files = [
        "/mnt/user-data/uploads/markscheme1.pdf",
        "/mnt/user-data/uploads/markscheme2.pdf",
        "/mnt/user-data/uploads/markscheme3.pdf"
    ]
    
    # Batch-Processing mit hoher Qualität
    results = crop_all_pdfs(
        pdf_files,
        output_base_dir="/home/claude/final_question_crops",
        resolution=300,  # Hohe Qualität
        margin=10,       # 10px Rand
        start_page=5     # Überspringe Metadaten
    )
    
    # Vergleich
    compare_crops(results)
    
    print("\n🎉 FERTIG! Alle Question-Crops wurden erstellt.")
    print("📂 Siehe: /home/claude/final_question_crops/")
