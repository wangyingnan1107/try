import os
import sys
import requests
import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

# Add libs directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))

try:
    from paddleocr import PaddleOCR
except ImportError:
    logging.warning("PaddleOCR not found. OCR functionality will be disabled.")
    PaddleOCR = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self, use_gpu: bool = False):
        """
        Initialize PaddleOCR service.
        :param use_gpu: Whether to use GPU for inference (requires CUDA).
        """
        if PaddleOCR:
            try:
                self.ocr = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=use_gpu, show_log=False)
                self.enabled = True
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}")
                self.enabled = False
        else:
            self.enabled = False
            
        self.executor = ThreadPoolExecutor(max_workers=3)

    def download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL."""
        try:
            # Handle local file paths if necessary, but assume URL for now
            if not url.startswith('http'):
                return None
                
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
        return None

    def extract_text_from_image(self, image_content: bytes) -> str:
        """Run OCR on image bytes."""
        if not self.enabled:
            return ""
            
        try:
            # PaddleOCR expects file path or numpy array. 
            # We can save to temp file or convert bytes to numpy array.
            # For simplicity and robustness, let's save to a temp file.
            import tempfile
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(image_content)
                tmp_path = tmp.name
            
            try:
                result = self.ocr.ocr(tmp_path, cls=True)
                # result structure: [[[[points], [text, score]], ...]]
                if not result or result[0] is None:
                    return ""
                
                texts = [line[1][0] for line in result[0]]
                return "\n".join(texts)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def process_images(self, image_urls: List[str]) -> str:
        """
        Process a list of image URLs and return combined text.
        """
        if not self.enabled or not image_urls:
            return ""
            
        combined_text = []
        
        # Process sequentially to avoid OOM on server, or use executor if powerful enough
        for i, url in enumerate(image_urls):
            logger.info(f"Processing OCR for image {i+1}/{len(image_urls)}")
            img_content = self.download_image(url)
            if img_content:
                text = self.extract_text_from_image(img_content)
                if text:
                    combined_text.append(f"--- 图片 {i+1} ---\n{text}")
        
        return "\n\n".join(combined_text)

# Singleton instance
ocr_service = OCRService(use_gpu=False)
