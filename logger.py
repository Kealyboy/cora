"""Logging for CORA."""

import logging
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("cora.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("CORA")

def log_info(msg: str) -> None:
    logger.info(msg)

def log_warning(msg: str) -> None:
    logger.warning(msg)

def log_error(msg: str) -> None:
    logger.error(msg)

def log_debug(msg: str) -> None:
    logger.debug(msg)

def log_conversation(user_input: str, layer: str, response: str) -> None:
    logger.info(f"USER: {user_input}")
    logger.info(f"LAYER: {layer}")
    logger.info(f"CORA: {response}")