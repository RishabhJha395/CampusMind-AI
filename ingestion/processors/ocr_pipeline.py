import logging
import io
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

class OCRPipeline:
    def __init__(self, languages: list[str] = None):
        # Default to English if none specified
        self.languages = languages or ["eng"]
        self.lang_string = "+".join(self.languages)
        
        self.is_available = True
        try:
            # Check if tesseract is installed by requesting version
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            logger.warning(
                "Tesseract is not installed or not in PATH! "
                "OCR pipeline will gracefully skip image extraction."
            )
            self.is_available = False
        except Exception as e:
            logger.warning(f"Failed to initialize Tesseract: {e}")
            self.is_available = False

    def process_image_bytes(self, image_bytes: bytes) -> str:
        """
        Process raw image bytes and return extracted text.
        Includes basic image pre-processing for better OCR.
        """
        if not self.is_available:
            return ""
            
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Basic preprocessing: convert to grayscale
            image = image.convert("L")
            
            # We could add binarization/deskew here in the future
            # e.g., image = image.point(lambda x: 0 if x < 128 else 255, '1')
            
            # Extract text
            text = pytesseract.image_to_string(
                image, 
                lang=self.lang_string,
                config="--psm 3" # Fully automatic page segmentation
            )
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return ""
