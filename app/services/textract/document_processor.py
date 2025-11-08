import io
import os
from typing import List, Tuple
from PIL import Image
from pdf2image import convert_from_path

class DocumentProcessor:
    SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.tiff', '.tif']
    SUPPORTED_PDF_FORMAT = '.pdf'

    @staticmethod
    def is_pdf(file_path: str) -> bool:
        _, ext = os.path.splitext(file_path)
        return ext.lower() == DocumentProcessor.SUPPORTED_PDF_FORMAT

    @staticmethod
    def is_image(file_path: str) -> bool:
        _, ext = os.path.splitext(file_path)
        return ext.lower() in DocumentProcessor.SUPPORTED_IMAGE_FORMATS

    @staticmethod
    def convert_pdf_to_images(pdf_path: str, dpi: int = 300) -> List[Image.Image]:
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
            return images
        except Exception as e:
            raise Exception(f"Failed to convert PDF to images: {str(e)}")

    @staticmethod
    def load_image(image_path: str) -> Image.Image:
        try:
            image = Image.open(image_path)
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')
            return image
        except Exception as e:
            raise Exception(f"Failed to load image: {str(e)}")

    @staticmethod
    def image_to_bytes(image: Image.Image, format: str = 'PNG') -> bytes:
        try:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=format)
            img_byte_arr.seek(0)
            return img_byte_arr.read()
        except Exception as e:
            raise Exception(f"Failed to convert image to bytes: {str(e)}")

    @staticmethod
    def process_document(file_path: str) -> Tuple[List[bytes], int]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        image_bytes_list = []

        if DocumentProcessor.is_pdf(file_path):
            images = DocumentProcessor.convert_pdf_to_images(file_path)
            for image in images:
                image_bytes = DocumentProcessor.image_to_bytes(image)
                image_bytes_list.append(image_bytes)
            page_count = len(images)

        elif DocumentProcessor.is_image(file_path):
            image = DocumentProcessor.load_image(file_path)
            image_bytes = DocumentProcessor.image_to_bytes(image)
            image_bytes_list.append(image_bytes)
            page_count = 1

        else:
            raise ValueError(f"Unsupported file format. Supported: PDF, {', '.join(DocumentProcessor.SUPPORTED_IMAGE_FORMATS)}")

        return image_bytes_list, page_count
