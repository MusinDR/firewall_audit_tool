# infrastructure/logger.py

import logging
import os

log_file_path = "logs/app.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logger = logging.getLogger("audit_gui")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
