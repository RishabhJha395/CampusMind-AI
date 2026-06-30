import logging
import fitz  # PyMuPDF
import pdfplumber
import os
from typing import List
from ingestion.processors.ocr_pipeline import OCRPipeline

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, languages: list[str] = None):
        self.ocr_pipeline = OCRPipeline(languages=languages)

    def process_pdf(self, file_path: str) -> str:
        """
        Extracts text from a local PDF file using a multi-stage approach.
        1. PyMuPDF for native text.
        2. Tesseract OCR for image-based pages.
        3. pdfplumber for table extraction.
        Returns a single concatenated markdown-like string.
        """
        if not os.path.exists(file_path):
            logger.error(f"PDF file not found: {file_path}")
            return ""

        full_text = []

        try:
            # 1. Open with PyMuPDF
            doc = fitz.open(file_path)
            logger.info(f"Processing PDF with {len(doc)} pages: {file_path}")
            
            # We will also use pdfplumber for tables
            with pdfplumber.open(file_path) as plumber_doc:
                
                for page_num in range(len(doc)):
                    page_text_blocks = []
                    
                    # Stage A: Native Text
                    page = doc[page_num]
                    native_text = page.get_text("text").strip()
                    
                    if native_text:
                        page_text_blocks.append(native_text)
                    else:
                        # Stage B: OCR fallback
                        # Extract images from page or render page as image
                        # Rendering the entire page at 300 DPI is usually safer
                        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                        img_bytes = pix.tobytes("png")
                        
                        ocr_text = self.ocr_pipeline.process_image_bytes(img_bytes)
                        if ocr_text:
                            page_text_blocks.append(f"*[OCR Extracted]*\n{ocr_text}")
                            
                    # Stage C: Table Extraction
                    # Check if there are tables
                    if page_num < len(plumber_doc.pages):
                        plumber_page = plumber_doc.pages[page_num]
                        tables = plumber_page.extract_tables()
                        if tables:
                            for table in tables:
                                # Convert table to simple markdown string
                                md_table = []
                                for row in table:
                                    cleaned_row = [str(cell).replace('\n', ' ') if cell else "" for cell in row]
                                    md_table.append(" | ".join(cleaned_row))
                                
                                table_str = "\n".join(md_table)
                                page_text_blocks.append(f"*[Extracted Table]*\n{table_str}")

                    # Combine page content
                    if page_text_blocks:
                        page_content = "\n\n".join(page_text_blocks)
                        full_text.append(f"--- Page {page_num + 1} ---\n{page_content}")

        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}: {e}")
            
        return "\n\n".join(full_text)
