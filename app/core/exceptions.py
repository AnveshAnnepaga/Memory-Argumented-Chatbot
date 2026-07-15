# File: app/core/exceptions.py
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base domain exception for the application."""
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationException(AppException):
    """Validation error exception."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class ResourceNotFoundException(AppException):
    """Resource not found exception."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class DatabaseException(AppException):
    """SQL or NoSQL database error exception."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details=details,
        )


class PineconeException(AppException):
    """Vector storage / Pinecone API error exception."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="PINECONE_ERROR",
            status_code=502,
            details=details,
        )


class Neo4jException(AppException):
    """Graph storage / Neo4j error exception."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="NEO4J_ERROR",
            status_code=502,
            details=details,
        )


class GroqException(AppException):
    """LLM / Groq API error exception."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="GROQ_ERROR",
            status_code=502,
            details=details,
        )


class RepositoryException(AppException):
    """General repository layer error exception translated from underlying infrastructure."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="REPOSITORY_ERROR",
            status_code=500,
            details=details,
        )


class RepositoryNotFoundException(ResourceNotFoundException):
    """Repository entity not found exception."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details,
        )
        self.code = "REPOSITORY_ENTITY_NOT_FOUND"

