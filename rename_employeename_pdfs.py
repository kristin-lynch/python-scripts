#!/usr/bin/env python3
"""
PDF Renamer - Extracts 'Employee Name' from Mercyhurst Prep Employee Handbook Acknowledgement PDFs and renames files
Author: Kristin Lynch
Date: 2025-10-15
"""

import os
import re
import PyPDF2
from pathlib import Path

def extract_name_from_pdf(pdf_path):
    """Extract the 'Name of User' field from the PDF."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Search through all pages for the name
            for page in reader.pages:
                text = page.extract_text()
                
                # Look for "Name of User" followed by the actual name
                match = re.search(r'Employee Name\s*\n\s*([A-Za-z\s]+)', text)
                if match:
                    name = match.group(1).strip()
                    # Clean up the name (remove extra spaces, newlines)
                    name = ' '.join(name.split())
                    return name
                    
        return None
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

def sanitize_filename(name):
    """Convert name to a safe filename format."""
    # Replace spaces with underscores or hyphens as preferred
    safe_name = name.replace(' ', '_')
    # Remove any characters that aren't alphanumeric, underscore, or hyphen
    safe_name = re.sub(r'[^\w\-]', '', safe_name)
    return safe_name

def rename_pdfs_in_folder(folder_path):
    """Rename all PDFs in the folder based on extracted names."""
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Folder not found: {folder_path}")
        return
    
    # Get all PDF files matching the pattern
    pdf_files = list(folder.glob("Employee Handbook Acknowledgement - *.pdf"))
    
    if not pdf_files:
        print("No matching PDF files found in the folder.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process.\n")
    
    renamed_count = 0
    failed_count = 0
    
    for pdf_file in sorted(pdf_files):
        print(f"Processing: {pdf_file.name}")
        
        # Extract the name from the PDF
        user_name = extract_name_from_pdf(pdf_file)
        
        if user_name:
            # Create new filename
            safe_name = sanitize_filename(user_name)
            new_filename = f"MPS-2025-Employee-Handbook-{safe_name}.pdf"
            new_path = pdf_file.parent / new_filename
            
            # Check if file already exists
            if new_path.exists():
                print(f"  ⚠️  File already exists: {new_filename}")
                failed_count += 1
            else:
                # Rename the file
                pdf_file.rename(new_path)
                print(f"  ✅ Renamed to: {new_filename}")
                renamed_count += 1
        else:
            print(f"  ❌ Could not extract name from file")
            failed_count += 1
        
        print()
    
    print(f"\n{'='*60}")
    print(f"Summary: {renamed_count} files renamed, {failed_count} failed")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Set the folder path - update this to your actual folder path
    folder_path = "/Users/kristin/Downloads/new folder"
    
    print("Mercyhurst Prep PDF Renamer")
    print("="*60)
    print(f"Target folder: {folder_path}\n")
    
    rename_pdfs_in_folder(folder_path)
