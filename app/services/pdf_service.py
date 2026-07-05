import logging
import os

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

logger = logging.getLogger(__name__)

class PDFService:
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extracts raw text from a PDF file.
        """
        if not fitz:
            logger.error("Dependencies missing. Run `pip install pymupdf`")
            return "Error: Missing dependencies. Please install pymupdf."

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return "Error: The specified PDF file does not exist."

        try:
            doc = fitz.open(file_path)
            extracted_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                extracted_text.append(page_text)
                
            doc.close()
            
            # Combine all pages and clean up excessive whitespace
            full_text = " ".join(extracted_text)
            clean_text = " ".join(full_text.split())
            
            if not clean_text:
                return "Error: Could not extract any readable text from this PDF (it may be an image-based scan)."
                
            return clean_text
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            return f"Error: Could not read PDF file. ({str(e)})"
