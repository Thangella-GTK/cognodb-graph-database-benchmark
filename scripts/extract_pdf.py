import sys
import pathlib
from PyPDF2 import PdfReader

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract_pdf.py <pdf-path> [out-txt]")
        sys.exit(1)
    pdf_path = pathlib.Path(sys.argv[1])
    out_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path('docs/assignment.txt')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(pdf_path))
    pages = []
    for p in reader.pages:
        pages.append(p.extract_text() or '')
    out_path.write_text('\n\n'.join(pages), encoding='utf-8')
    print(f"Wrote extracted text to {out_path}")

if __name__ == '__main__':
    main()
