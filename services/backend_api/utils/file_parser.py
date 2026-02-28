
import io
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Union

# Optional dependencies - handle gracefully if missing
try:
    from striprtf.striprtf import rtf_to_text
except ImportError:
    rtf_to_text = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import extract_msg
except ImportError:
    extract_msg = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

try:
    from odf.opendocument import load
    from odf import text as odf_text
    from odf import teletype
except ImportError:
    load = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None


def extract_text(file_path: Union[str, Path]) -> str:
    """Synchronous text extraction from a file on disk.

    This wraps the same logic as ``extract_text_from_upload`` but reads
    the file from a local path instead of an in-memory upload object,
    so parsers that operate on local files can use it directly.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return ""

    try:
        raw_bytes = file_path.read_bytes()
    except OSError:
        return ""

    import asyncio

    async def _run():
        return await extract_text_from_upload(raw_bytes, file_path.name)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an async context — use a new thread to avoid deadlock
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(_run())).result(timeout=30)
    else:
        return asyncio.run(_run())


async def extract_text_from_upload(uploaded_file, filename: str) -> str:
    """
    Convert an uploaded file (bytes) to plain text.
    Adapts legacy logic for FastAPI UploadFile/bytes.
    """
    # Read bytes from FastAPI UploadFile or bytes object
    if hasattr(uploaded_file, "read"):
        file_bytes = await uploaded_file.read()
    else:
        file_bytes = uploaded_file

    suffix = Path(filename).suffix.lower().strip()

    # -------------------------
    # Plain text-like formats
    # -------------------------
    if suffix in {'.txt', '.md', '.markdown', '.log'}:
        return file_bytes.decode('utf-8', errors='ignore')

    if suffix in {'.rtf'}:
        if rtf_to_text:
            try:
                return rtf_to_text(file_bytes.decode('utf-8', errors='ignore')).strip()
            except Exception:
                pass
        # Fallback
        raw = file_bytes.decode('utf-8', errors='ignore')
        raw = re.sub(r'\\[a-zA-Z]+\d* ?',' ', raw)
        raw = re.sub(r'[{}]', ' ', raw)
        return re.sub(r'\s+', ' ', raw).strip()

    if suffix in {'.html', '.htm'}:
        html = file_bytes.decode('utf-8', errors='ignore')
        if BeautifulSoup:
            try:
                return BeautifulSoup(html, "html.parser").get_text("\n").strip()
            except Exception:
                pass
        # Fallback
        text = re.sub(r'<[^>]+>', ' ', html)
        return re.sub(r'\s+', ' ', text).strip()

    # -------------------------
    # ZIP
    # -------------------------
    if suffix == '.zip':
        combined = []
        try:
            zf = zipfile.ZipFile(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Unable to read ZIP archive: {e}")

        max_files = 15
        max_total_chars = 200000
        count = 0

        for info in zf.infolist():
            if info.is_dir():
                continue
            count += 1
            if count > max_files:
                combined.append("\n[ZIP] ...additional files omitted...\n")
                break
            
            try:
                inner_bytes = zf.read(info)
                # Recursively extract (simplified for now, assume text/common formats)
                # In a real recursor we would call extract_text_from_upload again, 
                # but async makes recursion tricky without refactoring. 
                # For now, treat inner files as text if possible or skip.
                try:
                    text = inner_bytes.decode('utf-8', errors='ignore')
                    combined.append(f"\n----- FILE: {info.filename} -----\n{text}")
                except:
                    combined.append(f"\n----- FILE: {info.filename} (Binary skipped) -----\n")
            except Exception:
                continue
        
        return "\n".join(combined).strip()

    # -------------------------
    # PDF
    # -------------------------
    if suffix == '.pdf':
        if not PdfReader:
            raise RuntimeError("PyPDF2 not installed")
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            pages = [page.extract_text() or '' for page in reader.pages]
            return "\n".join(pages).strip()
        except Exception as exc:
            raise RuntimeError(f"PDF extraction failed: {exc}") from exc

    # -------------------------
    # DOCX
    # -------------------------
    if suffix == '.docx':
        if not docx:
            raise RuntimeError("python-docx not installed")
        try:
            document = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [para.text for para in document.paragraphs]
            return "\n".join(paragraphs).strip()
        except Exception as exc:
            raise RuntimeError(f"DOCX extraction failed: {exc}") from exc

    # -------------------------
    # Images (OCR)
    # -------------------------
    if suffix in {'.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff'}:
        if not Image or not pytesseract:
            raise RuntimeError("OCR (Pillow/pytesseract) not available")
        try:
            img = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(img) or ""
            return text.strip()
        except Exception as exc:
            raise RuntimeError(f"OCR failed: {exc}") from exc

    return ""
