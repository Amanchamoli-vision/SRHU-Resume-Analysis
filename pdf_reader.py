# pdf_reader.py — Extract text from PDF resumes

import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.

    Args:
        pdf_path (str): Path to PDF file

    Returns:
        str: Extracted text, or error string
    """
    extracted_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    extracted_text += f"\n\n--- Page {page_number} ---\n"
                    extracted_text += page_text

        return extracted_text.strip()

    except FileNotFoundError:
        return ""

    except Exception as error:
        print(f"❌ PDF Read Error: {error}")
        return ""