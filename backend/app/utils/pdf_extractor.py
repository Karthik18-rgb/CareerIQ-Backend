"""
PDF text extraction utility using PyMuPDF.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text content from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text as a string.

    Raises:
        ValueError: If the file cannot be read or contains no extractable text.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF is required for PDF extraction. Install with: pip install pymupdf"
        )

    path = Path(file_path)
    if not path.exists():
        raise ValueError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {file_path}")

    text_pages = []
    try:
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text.strip():
                text_pages.append(page_text)
        doc.close()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    full_text = "\n\n".join(text_pages).strip()
    if not full_text:
        raise ValueError("No extractable text found in the PDF. The file may be scanned images only.")

    logger.info("Extracted %d characters from PDF", len(full_text))
    return full_text
