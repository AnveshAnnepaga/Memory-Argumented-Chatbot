# File: app/core/bootstrap.py
import logging
import sys
from typing import Any, Dict
from fastapi import FastAPI
from app.ai.llm.llm_manager import llm_manager
from app.core.config import settings
from app.core.infrastructure import InfrastructureRegistry
from app.database.mongodb import mongo_manager
from app.database.neo4j import neo4j_manager
from app.database.pinecone import pinecone_manager
from app.database.postgres import postgres_manager

logger = logging.getLogger("app.core.bootstrap")


class BootstrapManager:
    """
    (`Bootstrap Manager` & `6.10 Bootstrap Integration`)
    Orchestrates application initialization, infrastructure lifecycle registration,
    startup validation, and clean teardown during shutdown events.
    """

    @classmethod
    def initialize_logging(cls) -> None:
        """Sets up application-wide logging handlers and formatting based on settings."""
        log_cfg = settings.logging
        handlers = []

        # Console handler
        if log_cfg.console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            handlers.append(console_handler)

        # File handler
        if log_cfg.file_logging and log_cfg.file_path:
            try:
                file_handler = logging.FileHandler(log_cfg.file_path, encoding="utf-8")
                handlers.append(file_handler)
            except Exception as e:
                print(f"Warning: Could not initialize file logging at {log_cfg.file_path}: {e}")

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | [%(name)s] | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        for handler in handlers:
            handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_cfg.level.value, logging.INFO))
        root_logger.handlers.clear()
        for handler in handlers:
            root_logger.addHandler(handler)

        logger.info(f"Logging initialized successfully [Level: {log_cfg.level.value} | File: {log_cfg.file_path}]")

    @classmethod
    def validate_environment(cls) -> Dict[str, bool]:
        """Validates critical environment variables (`5.12 Startup Validation`)."""
        logger.info("Performing startup environment and configuration validation...")
        checks = {
            "config_loaded": True,
            "secret_key_safe": settings.SECRET_KEY != "change-me-in-production-super-secret-key"
            or settings.APP_ENV != "production",
            "groq_key_configured": bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here"),
            "pinecone_key_configured": bool(settings.PINECONE_API_KEY and settings.PINECONE_API_KEY != "your_pinecone_api_key_here"),
        }

        if not checks["secret_key_safe"]:
            logger.warning("WARNING: Default SECRET_KEY detected in production. Set a secure key in Railway dashboard.")

        if not checks["groq_key_configured"]:
            logger.warning("GROQ_API_KEY is currently placeholder/empty. LLM Manager will operate in mock/fallback mode.")

        logger.info(f"Environment validation checks completed: {checks}")
        return checks

    @classmethod
    def register_infrastructure(cls) -> None:
        """
        (`6.6 Infrastructure Registry`)
        Registers every external database and LLM service manager into the global registry during startup.
        """
        logger.info("Registering external infrastructure services into InfrastructureRegistry...")
        InfrastructureRegistry.register("postgres", postgres_manager)
        InfrastructureRegistry.register("mongodb", mongo_manager)
        InfrastructureRegistry.register("pinecone", pinecone_manager)
        InfrastructureRegistry.register("neo4j", neo4j_manager)
        InfrastructureRegistry.register("groq", llm_manager)
        InfrastructureRegistry.register("llm", llm_manager)  # Alias for generic access
        logger.info(f"Registered services: {InfrastructureRegistry.list_services()}")

    @classmethod
    async def verify_dependencies(cls) -> Dict[str, Any]:
        """(`6.7 Health Integration`) Verifies real diagnostics of all registered infrastructure."""
        logger.info("Running diagnostic health verification on all infrastructure targets...")
        report = await InfrastructureRegistry.health_check_all()
        logger.info(f"Infrastructure health verification status: {report['overall_status']}")
        return report

    @classmethod
    async def startup(cls, app: FastAPI) -> None:
        """
        (`6.10 Bootstrap Integration`)
        Executed during FastAPI application startup:
        Initialize -> Validate -> Register -> Initialize All Services -> Verify Health -> Ready.
        """
        cls.initialize_logging()
        logger.info(f"--- Starting up {settings.APP_NAME} v{settings.APP_VERSION} ({settings.APP_ENV}) ---")
        cls.validate_environment()
        cls.register_infrastructure()

        # Initialize PostgreSQL, MongoDB, Pinecone, Neo4j, Groq (`6.10 Bootstrap Integration`)
        await InfrastructureRegistry.initialize_all()
        await cls.verify_dependencies()

        app.state.ready = True
        logger.info("=== Bootstrap Manager completed: Application and Infrastructure READY ===")

    @classmethod
    async def shutdown(cls, app: FastAPI) -> None:
        """
        (`6.9 Connection Lifecycle` & `5.13 Shutdown Validation`)
        Executed during FastAPI application shutdown: closes connection pools cleanly.
        """
        logger.info(f"--- Shutting down {settings.APP_NAME} ---")
        app.state.ready = False
        logger.info("Closing all external infrastructure connections and releasing pools...")
        await InfrastructureRegistry.close_all()
        logger.info("=== Shutdown completed cleanly. Goodbye! ===")
