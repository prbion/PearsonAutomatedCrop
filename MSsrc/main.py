from question_cropper import ImprovedQuestionCropper
from pathlib import Path

print("="*70)
print("PDF QUESTION CROPPER")
print("="*70)

# ============================================================
# METADATEN ABFRAGEN
# ============================================================
print("\nBitte gib die Informationen zum Marking Scheme ein:\n")

publisher = input("What Publisher? ").strip()
level = input("What Level? ").strip()
subject = input("What Subject? ").strip()
year = input("What Year? ").strip()

# PDF Pfad abfragen
print("\n" + "-"*70)
pdf_pfad = r"C:\Dev\MSsrc\markscheme1.pdf"

# ============================================================
# OPTIONAL: Einstellungen
# ============================================================
start_seite = 5      # Fist page to start scanning for questions
qualitaet = 300      # DPI
rand = 10            # Pixel Rand


# ============================================================
# ORDNERSTRUKTUR ERSTELLEN: Publisher/Subject/Year/
# ============================================================
# Ersetze Leerzeichen mit Unterstrichen für Ordnernamen
publisher_clean = publisher.replace(" ", "_")
subject_clean = subject.replace(" ", "_")
year_clean = year.replace(" ", "_")
level_clean = level.replace(" ", "_")

# Erstelle Ordnerstruktur
output_base = Path(f"{publisher_clean}/{subject_clean}/{year_clean}")
output_base.mkdir(parents=True, exist_ok=True)

print("\n" + "="*70)
print(" KONFIGURATION")
print("="*70)
print(f"Publisher: {publisher}")
print(f"Level: {level}")
print(f"Subject: {subject}")
print(f"Year: {year}")
print(f"PDF: {pdf_pfad}")
print(f"Output: {output_base}/")
print(f"Resolution: {qualitaet} DPI")
print("="*70)


# ============================================================
# QUESTION CROPPER AUSFÜHREN
# ============================================================
print("\n Starte Question Cropper...\n")

try:
    # create cropper instance
    cropper = ImprovedQuestionCropper(pdf_pfad, resolution=qualitaet)
    
    # extract questions
    crops = cropper.extract_all_questions(
        output_dir=str(output_base),
        start_page=start_seite,
        include_header=True,
        margin=rand
    )
    
    # ============================================================
    # DATEIEN UMBENENNEN MIT METADATEN
    # ============================================================
    print("\n Naming the cropped files with metadata...\n")
    
    renamed_files = []
    for crop_file in crops:
        # extract the old name (e.g. "question_1a.png")
        old_name = crop_file.name
        question_id = old_name.replace("question_", "").replace(".png", "")
        
        # Create new name with metadata
        # Format: Publisher_Subject_Year_Level_question_1a.png
        new_name = f"{publisher_clean}_{subject_clean}_{year_clean}_{level_clean}_question_{question_id}.png"
        
        # Umbenennen
        new_path = crop_file.parent / new_name
        crop_file.rename(new_path)
        renamed_files.append(new_path)
        
        print(f" {new_name}")
    
    # ============================================================
    # ERFOLGS-MELDUNG
    # ============================================================
    print("\n" + "="*70)
    print(" DONE!")
    print("="*70)
    print(f" {len(renamed_files)} Questions successfully cropped and renamed.")
    print(f" Folder: {output_base}/")
    print(f"\n  Data format:")
    print(f"   {publisher_clean}_{subject_clean}_{year_clean}_{level_clean}_question_[ID].png")
    print(f"\n example:")
    if renamed_files:
        print(f"   {renamed_files[0].name}")
    print("="*70)
    
except FileNotFoundError:
    print(f"\n ERROR: PDF NOT FOUND!")
    print(f"   Path: {pdf_pfad}")
    print(f"   Give a valid PDF path and try again.")
    
except Exception as e:
    print(f"\n ERROR: {e}")
    import traceback
    traceback.print_exc()
    print(f"\n   Tipp: Prüfe Dependencies:")
    print(f"   pip install pdfplumber pypdf pdf2image pillow --break-system-packages")
