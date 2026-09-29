import os
from PyPDF2 import PdfReader

def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extracts text from a PDF file.

    Args:
        file_path (str): The path to the PDF file.
    """
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return {"text": text.strip(), "page_count": str(len(reader.pages)), "word_count": str(len(text.split()))}

def extract_text_from_txt(file_path: str) -> str:
    """
    Extracts text from a TXT file.

    Args:
        file_path (str): The path to the TXT file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text =  f.read()
        
    return {"text": text.strip(), "page_count": "1", "word_count": str(len(text.split()))}

def extract_text(file_path: str) -> str:
    """
    Extracts text from a document file.

    Args:
        file_path (str): The path to the document file.
    """

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError("Unsupported file type. Only PDF and TXT files are allowed.")