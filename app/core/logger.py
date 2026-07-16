"""
Core Logging Utility

Provides standardized logger instantiation across the entire FastAPI & LangGraph backend.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """Returns a standard Python logging.Logger instance configured for the application."""
    return logging.getLogger(name)
