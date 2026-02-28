import os
import time
import logging
import threading
import json
import asyncio
from pathlib import Path
from typing import Set

from services.backend_api.utils.file_parser import extract_text_from_upload

logger = logging.getLogger("processor")

class ResumeProcessor:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.data_root = os.getenv("CAREERTROJAN_DATA_ROOT", "/data/ai_data_final")
        self.parser_dir = os.path.join(self.data_root, "automated_parser")
        self.output_dir = Path(self.data_root) / "ai_data_final"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.processed_files: Set[str] = set()

    def start_monitoring(self):
        """Monitors the automated_parser directory for new files."""
        if not os.path.exists(self.parser_dir):
            logger.error(f"Parser directory NOT FOUND: {self.parser_dir}")
            return

        logger.info(f"Monitoring directory: {self.parser_dir}")
        
        while True:
            try:
                self._scan_directory()
                time.sleep(5) # Poll every 5 seconds
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(5)

    def _scan_directory(self):
        """Scans for new files and processes them."""
        for filename in os.listdir(self.parser_dir):
            if filename.startswith('.'): continue # Skip hidden files
            
            filepath = os.path.join(self.parser_dir, filename)
            if not os.path.isfile(filepath): continue
            
            if filename in self.processed_files: continue

            logger.info(f"Detected new file: {filename}")
            self._process_file(filepath, filename)
            self.processed_files.add(filename)

    def _process_file(self, filepath: str, filename: str):
        """Parse a resume file into ai_data_final JSON."""
        logger.info(f"Processing {filename}...")
        file_path = Path(filepath)
        try:
            file_bytes = file_path.read_bytes()
            text = asyncio.run(extract_text_from_upload(file_bytes, filename))
        except Exception as exc:
            logger.error(f"Parsing failed for {filename}: {exc}")
            return

        if not text:
            logger.error(f"No extractable text for {filename}")
            return

        payload = {
            "source_file": filename,
            "source_path": str(file_path),
            "file_type": file_path.suffix.lower().lstrip("."),
            "extracted_text": text,
            "processed_at": time.time(),
        }

        output_name = f"{file_path.stem}_{int(time.time() * 1000)}.json"
        output_path = self.output_dir / output_name
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info(f"Saved parsed output: {output_path}")
