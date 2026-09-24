import os
import sys
from loguru import logger

logger.configure(extra={"request_id": "-"})
logger.remove()
logger.add(
    sys.stdout,
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    diagnose=False,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {extra} | {message}",
    colorize=True,
)
logger.add(
    "./logs/thermal-server.log",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    diagnose=False,
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {extra} | {message}",
)
