# modules/utils.py
import io, base64, json
from pdf2image import convert_from_path
from PIL import Image

def pil_to_base64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def convert_pdf_to_images_safe(pdf_path: str, dpi: int = 200):
    """
    Convert each PDF page to a PIL.Image list.
    """
    return convert_from_path(pdf_path, dpi=dpi)

def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        import json
        return json.load(f)
