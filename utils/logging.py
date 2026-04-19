import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logging(app):
    log_dir = app.config.get("LOG_DIR", "logs")
    log_file = app.config.get("LOG_FILE", os.path.join(log_dir, "app.log"))
    max_bytes = app.config.get("LOG_MAX_BYTES", 10 * 1024 * 1024)
    backup_count = app.config.get("LOG_BACKUP_COUNT", 5)

    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # FILE HANDLER
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # CONSOLE HANDLER
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # 🔥 Configure ROOT logger (important)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    root_logger.info("Logging initialized successfully.")