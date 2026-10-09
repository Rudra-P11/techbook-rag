import fitz  # PyMuPDF
import io
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PIL import Image
from app.ingestion.cleaner import text_cleaner
from app.ingestion.ocr import ocr_service

logger = logging.getLogger(__name__)


class PDFLoader:
    def load_pdf(self, file_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extract text page-by-page from a PDF file.
        Returns (list_of_pages, metadata_summary).
        """
        doc = fitz.open(str(file_path))
        page_count = len(doc)
        pages_data = []

        scanned_count = 0
        native_count = 0

        for idx, page in enumerate(doc):
            page_num = idx + 1  # 1-based index
            rect = page.rect
            width, height = rect.width, rect.height

            # Try native extraction
            raw_text = page.get_text("text")
            extraction_method = "native"

            # Check if likely scanned and OCR is enabled on the system
            if ocr_service.is_available() and text_cleaner.is_likely_scanned(raw_text):
                try:
                    pix = page.get_pixmap(dpi=150)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = ocr_service.ocr_image(img)
                    if len(ocr_text) > len(raw_text.strip()):
                        raw_text = ocr_text
                        extraction_method = "ocr"
                        scanned_count += 1
                    else:
                        native_count += 1
                except Exception as e:
                    logger.warning(f"Failed OCR fallback on page {page_num}: {e}")
                    native_count += 1
            else:
                native_count += 1

            cleaned = text_cleaner.clean(raw_text)

            pages_data.append({
                "page_number": page_num,
                "text": cleaned,
                "extraction_method": extraction_method,
                "page_width": width,
                "page_height": height
            })

        summary = {
            "page_count": page_count,
            "scanned_pages": scanned_count,
            "native_pages": native_count,
            "format": doc.metadata.get("format", "PDF"),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", "")
        }
        doc.close()
        return pages_data, summary


pdf_loader = PDFLoader()
