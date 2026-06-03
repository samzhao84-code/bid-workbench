import os
from docx import Document


def parse_docx(filepath: str) -> str:
    """Parse a .docx file and return full plain text."""
    doc = Document(filepath)
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def parse_file(filepath: str, filename: str) -> str:
    """Parse uploaded file based on extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".docx":
        return parse_docx(filepath)
    elif ext == ".pdf":
        return parse_pdf(filepath)
    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def parse_pdf(filepath: str) -> str:
    """Parse a PDF file and return plain text."""
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-c", f"""
import sys
try:
    import PyPDF2
    reader = PyPDF2.PdfReader(r"{filepath}")
    text = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text.append(t)
    print("\\n".join(text))
except ImportError:
    print("PDF parsing requires PyPDF2. Please install: pip install PyPDF2")
"""],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return result.stderr.strip()
    except Exception as e:
        try:
            import fitz
            doc = fitz.open(filepath)
            text = []
            for page in doc:
                text.append(page.get_text())
            return "\n".join(text)
        except ImportError:
            return f"PDF parsing unavailable. Please install PyPDF2 or PyMuPDF. Error: {e}"
