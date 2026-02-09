import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("parser-worker")

def run():
    logger.info("Starting Parser Worker...")
    while True:
        logger.info("Checking for jobs...")
        time.sleep(10)

if __name__ == "__main__":
    run()
