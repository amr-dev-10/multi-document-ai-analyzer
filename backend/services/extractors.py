from pathlib import Path


def extract_pages(path: str, filename: str, content_type: str) -> list[dict]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf" or content_type == "application/pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix in {".xlsx", ".xls"}:
        return _extract_excel(path)
    if suffix in {".csv"}:
        return _extract_csv(path)
    if suffix in {".txt", ".md", ".log"} or content_type.startswith("text/"):
        return [{"page": 1, "text": Path(path).read_text(encoding="utf-8", errors="ignore")}]
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".tiff"}:
        return _extract_image(path)
    return [{"page": 1, "text": Path(path).read_text(encoding="utf-8", errors="ignore")}]


def _extract_pdf(path: str) -> list[dict]:
    import fitz

    pages = []
    with fitz.open(path) as doc:
        for idx, page in enumerate(doc, start=1):
            pages.append({"page": idx, "text": page.get_text("text")})
    return pages


def _extract_docx(path: str) -> list[dict]:
    from docx import Document

    doc = Document(path)
    blocks = [para.text for para in doc.paragraphs if para.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            blocks.append(" | ".join(cell.text.strip() for cell in row.cells))
    return [{"page": 1, "text": "\n".join(blocks)}]


def _extract_excel(path: str) -> list[dict]:
    import pandas as pd

    sheets = pd.read_excel(path, sheet_name=None)
    pages = []
    for idx, (name, frame) in enumerate(sheets.items(), start=1):
        pages.append({"page": idx, "text": f"Sheet: {name}\n{frame.to_csv(index=False)}"})
    return pages


def _extract_csv(path: str) -> list[dict]:
    import pandas as pd

    frame = pd.read_csv(path)
    return [{"page": 1, "text": frame.to_csv(index=False)}]


def _extract_image(path: str) -> list[dict]:
    try:
        import pytesseract
        from PIL import Image

        text = pytesseract.image_to_string(Image.open(path))
    except Exception:
        text = "Image uploaded. OCR engine is not installed locally, so no text could be extracted."
    return [{"page": 1, "text": text}]

