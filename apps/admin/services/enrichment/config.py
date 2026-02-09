import json
import logging
from pathlib import Path
from typing import Dict, Any

CONFIG_PATH = Path(__file__).parent.parent / 'enrichment_config.json'

def load_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"Failed to load enrichment config: {e}")
        return {}
