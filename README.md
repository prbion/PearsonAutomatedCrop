# PDF Question Extractor

A Python tool for automatically extracting and cropping individual questions from examination papers and educational PDFs. The tool intelligently identifies question boundaries, splits multi-part questions into sub-tasks, and saves them as organized, labeled image files.

## Features

- **Automated Question Detection**: Identifies questions using pattern matching for question numbers (e.g., "1.", "2.") and mark allocations (e.g., "(3)", "(5)")
- **Smart Cropping**: Automatically calculates optimal crop boundaries for each question part
- **Organized Output**: Generates structured filenames and folders based on publisher, level, subject, and year
- **High-Resolution Output**: Produces crisp images with 2x resolution scaling for better clarity
- **Batch Processing**: Processes entire PDF documents in a single run
- **Flexible Naming**: Supports alphabetical labeling for multi-part questions (a, b, c, etc.)

## Prerequisites

- Python 3.7 or higher
- Tesseract OCR (optional, included in imports but not actively used in current implementation)

## Installation

1. **Clone or download this repository**

2. **Install required Python packages:**

```bash
pip install pymupdf pillow pytesseract
```

3. **Install Tesseract OCR** (optional):
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

## Project Structure

```
pdf-question-extractor/
│
├── main.py              # Entry point and orchestration
├── Menu.py              # User input handler for metadata
├── PDFManager.py        # PDF file operations
├── TaskExtractor.py     # Question detection and boundary calculation
├── ImageSnipper.py      # Image cropping and saving
├── TaskPipeline.py      # Processing pipeline coordinator
└── README.md            # This file
```

## Usage

### Basic Usage

1. **Run the program:**

```bash
python main.py
```

2. **Provide the requested information:**
   - Publisher (e.g., "Edexcel", "AQA", "OCR")
   - Level (e.g., "GCSE", "AS", "A2")
   - Subject (e.g., "Maths", "Physics", "Chemistry")
   - Year (e.g., "2019", "2020")

3. **Configure the PDF path** in `main.py`:

```python
pdf_path = r"C:\path\to\your\exam_paper.pdf"
```

4. **Output files** will be saved in a folder named: `{Publisher}_{Subject}_{Year}/`

### Example

**Input:**
```
What Publisher? Edexcel
What Level? GCSE
What Subject? Maths
What Year? 2019
```

**Output Structure:**
```
Edexcel_Maths_2019/
├── Edexcel_GCSE_Maths_2019_1_a.png
├── Edexcel_GCSE_Maths_2019_1_b.png
├── Edexcel_GCSE_Maths_2019_2_a.png
└── ...
```

## How It Works

1. **Menu Input**: Collects metadata about the exam paper
2. **PDF Loading**: Opens and prepares the PDF for processing
3. **Question Detection**: 
   - Scans each page for question numbers (pattern: `\d+\.`)
   - Identifies mark allocations (pattern: `\(\d+\)`)
4. **Boundary Calculation**: Determines crop areas between mark indicators
5. **Image Extraction**: Crops and saves each question part as a high-resolution PNG
6. **Organized Storage**: Files are saved with descriptive names in a structured folder

## Configuration

### Modifying Detection Patterns

Edit `TaskExtractor.py` to adjust pattern matching:

```python
self.mark_pattern = r"\(\d+\)"      # Matches marks like (3), (5)
self.header_pattern = r"(\d+\.)"     # Matches question numbers like 1., 2.
```

### Adjusting Crop Boundaries

Modify crop parameters in `TaskExtractor.py`:

```python
right_side = page.rect.width * 0.85  # Crop to 85% of page width
bottom = y_coord + 10                # Buffer below mark indicator
```

### Resolution Settings

Change the scaling matrix in `ImageSnipper.py`:

```python
matrix=pymupdf.Matrix(2, 2)  # 2x scaling (higher = better quality, larger files)
```

## Class Overview

### Menu
Handles user input and generates consistent file and folder naming conventions.

### PDFManager
Manages PDF document lifecycle: opening, page navigation, and closing.

### TaskExtractor
Identifies questions and calculates optimal crop boundaries using regex pattern matching.

### ImageSnipper
Performs the actual image cropping and file saving operations.

### TaskPipeline
Orchestrates the entire extraction process, coordinating all components.

## Limitations

- Assumes consistent formatting within PDF (question numbers followed by mark allocations)
- Works best with single-column layouts
- Minimum crop height of 40 pixels to filter out false positives
- Alphabetical labels cycle after 'z' (for questions with 26+ parts)

## Troubleshooting

**No images are generated:**
- Verify the PDF path is correct
- Check that questions follow the expected numbering format
- Ensure mark allocations are in the format "(N)"

**Questions are cropped incorrectly:**
- Adjust the `right_side` percentage in `TaskExtractor.py`
- Modify the buffer values in `calculate_crop_areas()`

**File permission errors:**
- Ensure write permissions for the output directory
- Close any open image files before re-running

## Future Enhancements
- GUI interface for easier configuration
- Batch processing of multiple PDF files


## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check issues page if you want to contribute.

---

**Author**: Arbion Memaj  
**Last Updated**: February 2026
