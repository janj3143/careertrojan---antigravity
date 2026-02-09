import os
import json
import time
from loguru import logger

DATA_ROOT = os.getenv("CAREERTROJAN_DATA_ROOT", "/data/ai_data_final")
WORKING_ROOT = os.getenv("CAREERTROJAN_WORKING_ROOT", "/data/working_copy")
INTERACTIONS_LOG = os.path.join(WORKING_ROOT, "logs", "interactions", "interactions.jsonl")
LEARNING_STORES_DIR = os.path.join(WORKING_ROOT, "ai_json")

if not os.path.exists(LEARNING_STORES_DIR):
    os.makedirs(LEARNING_STORES_DIR, exist_ok=True)

class EnrichmentWorker:
    def __init__(self):
        self.trend_file = os.path.join(LEARNING_STORES_DIR, "keyword_trends.json")
        self.phrase_file = os.path.join(LEARNING_STORES_DIR, "learning_phrases.json")

    def process_interactions(self):
        """
        Periodically reads the interactions log and updates learning stores.
        """
        logger.info("Enrichment Worker started. Monitoring interactions...")
        
        while True:
            if os.path.exists(INTERACTIONS_LOG):
                try:
                    with open(INTERACTIONS_LOG, "r") as f:
                        lines = f.readlines()
                        # Simple simulation of process-only-new-lines
                        # In a real system, you'd use a cursor or separate queue
                        for line in lines[-10:]: # Look at last 10 for demo/sim
                            event = json.loads(line)
                            self.enrich_data(event)
                except Exception as e:
                    logger.error(f"Error processing interactions: {e}")
            
            time.sleep(60) # Run every minute

    def enrich_data(self, event):
        """
        Updates local working stores based on interaction deltas.
        """
        action = event.get("action_type")
        deltas = event.get("delta_summary", {})
        
        if deltas:
            logger.info(f"Enriching data from event {event['event_id']} (Action: {action})")
            # Logic to update phrase/trend JSON files would go here...
            # This ensures working_copy is updated, NOT ai_data_final directly.

if __name__ == "__main__":
    worker = EnrichmentWorker()
    worker.process_interactions()
