#!/usr/bin/env python3
"""Structured logging configuration for production deployments."""

import json
import logging
import logging.handlers
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing and indexing."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(name: str, log_file: str = None, level: str = "INFO"):
    """Setup structured logging for systemd integration."""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplication
    logger.handlers = []
    
    # Console handler (systemd journal auto-captures stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger
