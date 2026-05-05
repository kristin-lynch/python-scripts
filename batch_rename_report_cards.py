#!/usr/bin/env python3
"""
Batch-rename report-card PDFs to: flastyy.pdf
Improved OCR with image preprocessing for better accuracy.
"""

import re
import sys
from pathlib import Path

import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter


def preprocess_image_for_ocr(img: Image.Image) -> Image.Image:
    """
    Enhance image quality before OCR:
    - Convert to grayscale
    - Increase contrast
    - Sharpen
    - Apply threshold (make text darker, background whiter)
    """
    # Convert to grayscale
    img = img.convert('L')
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    
    # Apply threshold to make text more distinct
    # Convert to black & white (pixels below 150 become black, above become white)
    img = img.point(lambda x: 0 if x < 150 else 255, '1')
    
    return img


def ocr_first_page(pdf_path: Path) -> str | None:
    """
    OCR the first page with preprocessing for better accuracy.
    Uses higher DPI and image enhancement.
    """
    try:
        # Convert at higher resolution (400 DPI for better text recognition)
        images = convert_from_path(str(pdf_path), first_page=1, last_page=1, dpi=400)
        if not images:
            return None
        
        img: Image.Image = images[0]
        
        # Preprocess the image
        img = preprocess_image_for_ocr(img)
        
        # Use Tesseract with PSM 6 (assume uniform block of text)
        # and preserve more whitespace
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, lang="eng", config=custom_config)
        
        return text.strip() if text else None
        
    except Exception as e:
        print(f"⚠️ OCR failed for {pdf_path.name}: {e}")
        return None


def extract_student_info(text: str):
    """
    Extract student ID and name from OCR text.
    Returns (student_id, first_name, last_name) or (None, None, None).
    
    Looks for patterns like:
    - 6-digit ID: 226145
    - Name format: "Chen, Jieni" or "Chen, Jieni (Jenny)"
    """
    student_id = None
    first_name = None
    last_name = None
    
    # Find 6-digit student ID
    id_match = re.search(r'\b(\d{6})\b', text)
    if id_match:
        student_id = id_match.group(1)
    
    # Find name in "LastName, FirstName" format
    # More flexible pattern to handle OCR errors
    name_match = re.search(
        r'\b([A-Z][a-z]+),\s+([A-Z][a-z]+)(?:\s+\([^)]+\))?',
        text,
        re.MULTILINE
    )
    
    if name_match:
        last_name = name_match.group(1)
        first_name = name_match.group(2)
    
    return student_id, first_name, last_name


def build_filename(student_id: str, first_name: str, last_name: str) -> str | None:
    """
    Build filename: flastyy.pdf
    f = first initial, last = last name, yy = 2nd & 3rd digits of ID
    """
    if not all([student_id, first_name, last_name]):
        return None
    
    first_initial = first_name[0].lower()
    last_name_clean = last_name.lower()
    
    if len(student_id) >= 3:
        id_digits = student_id[1:3]
    else:
        return None
    
    return f"{first_initial}{last_name_clean}{id_digits}.pdf"


def sanitize(filename: str) -> str:
    """Remove invalid filename characters."""
    filename = filename.replace(" ", "_")
    filename = re.sub(r"[^a-zA-Z0-9_\-.]", "", filename)
    return filename


def batch_rename_report_cards(folder_path: Path, debug: bool = False):
    """
    Batch rename report cards with improved OCR.
    If debug=True, prints the raw OCR text for troubleshooting.
    """
    pdf_files = list(folder_path.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {folder_path}")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files\n")
    
    for pdf_path in pdf_files:
        try:
            # Try normal text extraction first
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                raw_text = first_page.extract_text()
            
            # Fall back to OCR if no embedded text
            if not raw_text or not raw_text.strip():
                print(f"ℹ️  No embedded text in {pdf_path.name}. Running OCR…")
                raw_text = ocr_first_page(pdf_path)
            
            if not raw_text:
                print(f"⚠️  Unable to obtain any text from {pdf_path.name}. Skipping.\n")
                continue
            
            # Debug mode: show what OCR extracted
            if debug:
                print(f"--- OCR OUTPUT for {pdf_path.name} ---")
                print(raw_text[:500])  # First 500 chars
                print("--- END OCR OUTPUT ---\n")
            
            # Extract student info
            student_id, first_name, last_name = extract_student_info(raw_text)
            
            if not all([student_id, first_name, last_name]):
                print(f"⚠️  Could not parse info from {pdf_path.name}")
                print(f"    Found: ID={student_id}, First={first_name}, Last={last_name}")
                if not debug:
                    print(f"    💡 Run with --debug to see OCR output\n")
                continue
            
            # Build filename
            new_name = build_filename(student_id, first_name, last_name)
            if not new_name:
                print(f"⚠️  Failed to build filename for {pdf_path.name}. Skipping.\n")
                continue
            
            new_name = sanitize(new_name)
            new_path = pdf_path.parent / new_name
            
            # Check for duplicates
            if new_path.exists():
                print(f"⚠️  Target {new_path.name} already exists. Skipping {pdf_path.name}.\n")
                continue
            
            # Rename
            pdf_path.rename(new_path)
            print(f"✅ {pdf_path.name} → {new_path.name}\n")
            
        except Exception as exc:
            print(f"💥 Error processing {pdf_path.name}: {exc}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Batch-rename report-card PDFs with OCR"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Folder containing PDFs (default: current directory)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show OCR output for troubleshooting"
    )
    
    args = parser.parse_args()
    target_folder = Path(args.folder).expanduser().resolve()
    
    if not target_folder.is_dir():
        print(f"❌ Folder '{target_folder}' does not exist.")
        sys.exit(1)
    
    batch_rename_report_cards(target_folder, debug=args.debug)