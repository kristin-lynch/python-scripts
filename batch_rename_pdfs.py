import pdfplumber
from pathlib import Path
import re
import unicodedata

def extract_username(text):
    """
    Extracts student info from the PDF content.
    Returns a filename in the format: lastnamefXX
    (last name + first initial + 2-digit grad year from student number)
    """
    # Match: [student number] LastName, FirstName [(Nickname)] Grade
    match = re.search(r'(\d{5,6})\s+([^,\n]+),\s+([^\n]+?)\s+\d{1,2}\s*(?:\n|$)', text)
    if match:
        student_number = match.group(1)
        last_name = match.group(2).strip().replace(' ', '')  # Compact compound surnames
        first_name_raw = re.sub(r'\s*\([^)]+\)', '', match.group(3)).strip()
        first_name = first_name_raw.split()[0]
        grad_year = student_number[1:3]  # 2nd and 3rd digits of student number
        return f"{last_name}{first_name[0]}{grad_year}"

    # Fall back to student ID
    match = re.search(r'\*\*\*studentid=(\d+)\*\*\*', text)
    if match:
        return match.group(1)

    # Legacy: PowerSchool username lookup
    if "PowerSchool" in text:
        powerschool_section = text[text.find("PowerSchool"):]
        match = re.search(r"username:\s*([a-zA-Z0-9\.]+)", powerschool_section)
        if match:
            return match.group(1)

    return None

def sanitize_filename(filename):
    """
    Removes or replaces invalid characters for filenames.
    Converts accented characters to their ASCII equivalents.
    """
    # Decompose accented characters to ASCII equivalents (e.g. ö→o, ä→a)
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    filename = filename.lower()
    filename = re.sub(r"[^a-z0-9_\-.]", "", filename)  # Remove remaining special characters
    return filename

def batch_rename_pdfs(folder_path):
    """
    Batch renames PDF files in a folder based on extracted content.
    """
    for pdf_file in Path(folder_path).glob("*.pdf"):
        try:
            with pdfplumber.open(pdf_file) as pdf:
                # Extract text from the first page
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                # Check if text extraction was successful
                if not text:
                    print(f"Warning: No text extracted from {pdf_file.name}. Skipping.")
                    continue
                
                # Extract the username
                new_name = extract_username(text)
                
                # Check if a username was found
                if not new_name:
                    print(f"Warning: No username found in {pdf_file.name}. Skipping.")
                    continue
                
                # Sanitize the filename
                new_name = sanitize_filename(new_name)
                
                # Check if new_name is empty after sanitization
                if not new_name:
                    print(f"Warning: New name is empty after sanitization for {pdf_file.name}. Skipping.")
                    continue
                
                # Rename the file
                new_path = pdf_file.parent / f"{new_name}.pdf"
                
                # Check if the new file name already exists
                if new_path.exists():
                    print(f"Warning: {new_path.name} already exists. Skipping {pdf_file.name}.")
                    continue
                
                pdf_file.rename(new_path)
                print(f"Renamed {pdf_file.name} to {new_path.name}")
                
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}")

# Example usage:
folder_path = "/Users/kristin/Downloads/new folder"  # Replace with the actual path
batch_rename_pdfs(folder_path)
