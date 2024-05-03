from convert_pdf_to_image import convert_to_images
from ocr import extract_text_from_images
from extract_predictions import extract_predictions

convert_to_images("to_convert", "images")
extract_text_from_images("images")
extract_predictions("ocr_tasks.json")
