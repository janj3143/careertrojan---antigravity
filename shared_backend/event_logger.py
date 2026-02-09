import os
import json
import time
import uuid
from loguru import logger

WORKING_ROOT = os.getenv("CAREERTROJAN_WORKING_ROOT", "/data/working_copy")
INTERACTIONS_LOG_DIR = os.path.join(WORKING_ROOT, "logs", "interactions")

if not os.path.exists(INTERACTIONS_LOG_DIR):
    os.makedirs(INTERACTIONS_LOG_DIR, exist_ok=True)

class InteractionLogger:
    def __init__(self):
        self.log_file = os.path.join(INTERACTIONS_LOG_DIR, "interactions.jsonl")

    def log_event(self, action_type, user_id=None, input_artifacts=None, output_artifacts=None, delta_summary=None):
        """
        Logs a meaningful user interaction event to an append-only JSONL file.
        """
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "user_id": user_id,
            "action_type": action_type,
            "input_artifacts": input_artifacts or [],
            "output_artifacts": output_artifacts or [],
            "delta_summary": delta_summary or {},
            "branding": "CareerTrojan"
        }
        
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
            logger.info(f"Interaction Logged: {action_type} - {event['event_id']}")
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")

# Global logger instance
interaction_logger = InteractionLogger()
