import logging

import os

# ==========================================
# CREATE LOGS DIRECTORY
# ==========================================

os.makedirs(
    "logs",
    exist_ok=True
)

# ==========================================
# LOGGER CONFIG
# ==========================================

logger = logging.getLogger(
    "TradingBot"
)

logger.setLevel(
    logging.INFO
)

# ==========================================
# FORMATTER
# ==========================================

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

# ==========================================
# RUNTIME LOG FILE
# ==========================================

runtime_handler = logging.FileHandler(
    "logs/runtime.log",
    encoding="utf-8"
)

runtime_handler.setLevel(
    logging.INFO
)

runtime_handler.setFormatter(
    formatter
)

# ==========================================
# ERROR LOG FILE
# ==========================================

error_handler = logging.FileHandler(
    "logs/errors.log",
    encoding="utf-8"
)

error_handler.setLevel(
    logging.ERROR
)

error_handler.setFormatter(
    formatter
)

# ==========================================
# CONSOLE OUTPUT
# ==========================================

console_handler = logging.StreamHandler()

console_handler.setLevel(
    logging.INFO
)

console_handler.setFormatter(
    formatter
)

# ==========================================
# ADD HANDLERS
# ==========================================

logger.addHandler(
    runtime_handler
)

logger.addHandler(
    error_handler
)

logger.addHandler(
    console_handler
)

# ==========================================
# LOGGER READY
# ==========================================

logger.info(
    "Logger initialized"
)