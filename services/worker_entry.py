import os
import time
import logging
import redis
import json
from services.ai_workers.processor import ResumeProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
SERVICE_NAME = os.getenv("SERVICE_NAME", "generic-worker")

def main():
    logger.info(f"Starting {SERVICE_NAME}...")
    
    # Initialize Redis Connection
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        logger.info("Connected to Redis")
    except redis.ConnectionError:
        logger.error("Failed to connect to Redis")
        return

    # Initialize Processor
    processor = ResumeProcessor(redis_client=r)

    if SERVICE_NAME == 'parser-worker':
        logger.info("Starting Parser Mode: Monitoring automated_parser")
        processor.start_monitoring()
    elif SERVICE_NAME == 'enrichment-worker':
        logger.info("Starting Enrichment Mode: Listening for jobs")
        # processor.start_enrichment_loop() # Future impl
        while True:
            time.sleep(10) # Keep alive
    else:
        logger.warning(f"Unknown service name: {SERVICE_NAME}")

if __name__ == "__main__":
    main()
