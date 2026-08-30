from __future__ import annotations

import sys

import pdfplumber

def extract_text(pdf_path: str) -> str:
    """Extract raw text from a screenplay PDF, one page at a time.
    
    Pages are joined with a page-break marker so downstream consumers
    can reason about page boundaries if useful, without this function
    making any assumptions about scene structure.
    """

    pages: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            pages.append(f"--- PAGE {i} ---\n\n{page_text}")

    return "\n\n".join(pages)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python extractor.py <path-to-screenplay.pdf>")
        sys.exit(1)

    raw_text = extract_text(sys.argv[1])
    print(raw_text)
    print(f"\n\n[extractor] {len(raw_text)} characters extracted.", file=sys.stderr)