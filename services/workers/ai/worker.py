import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-worker")

def run():
    logger.info("Starting AI Worker...")
    while True:
        logger.info("Checking for jobs...")
        time.sleep(10)

if __name__ == "__main__":
    run()
