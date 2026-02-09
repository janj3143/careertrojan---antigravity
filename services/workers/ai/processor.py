import os
import time
import logging
import threading
from typing import Set

logger = logging.getLogger("processor")

class ResumeProcessor:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.data_root = os.getenv("CAREERTROJAN_DATA_ROOT", "/data/ai_data_final")
        self.parser_dir = os.path.join(self.data_root, "automated_parser")
        self.processed_files: Set[str] = set()

    def start_monitoring(self):
        """Monitors the automated_parser directory for new files."""
        # For local testing if mount fails or is different in dev
        if not os.path.exists(self.parser_dir):
            # Try to recover or create if allowed (usually read-only mount though)
            logger.warning(f"Parser directory not found at {self.parser_dir}. Checking for local override...")
            # Fallback for dev environment without full mounts
            local_fallback = os.path.join(
                os.getenv("CAREERTROJAN_ROOT", os.getcwd()), "working", "automated_parser"
            )
            if os.path.exists(local_fallback):
                 self.parser_dir = local_fallback

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
        """Mock processing logic."""
        logger.info(f"Processing {filename}...")
        logger.info(f"Successfully processed {filename}")
