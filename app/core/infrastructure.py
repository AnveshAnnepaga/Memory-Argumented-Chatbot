# File: app/core/infrastructure.py
import abc
import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger("app.core.infrastructure")


class BaseInfrastructureManager(abc.ABC):
    """
    (`6.9 Connection Lifecycle`)
    Common abstract lifecycle contract enforced across all infrastructure components:
    Initialize -> Health Check -> Get Client -> Close Connection.
    """

    def __init__(self, name: str):
        self.name = name
        self._is_initialized = False

    @abc.abstractmethod
    async def initialize(self) -> bool:
        """Initializes client connections, connection pools, and verifies initial reachability."""
        pass

    @abc.abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Performs a live diagnostic check against the target service (`6.7 Health Integration`)."""
        pass

    @abc.abstractmethod
    def get_client(self) -> Any:
        """Returns the active driver or connection client."""
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        """Gracefully closes connection pools and cleans up resources."""
        pass

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized


class InfrastructureRegistry:
    """
    (`6.6 Infrastructure Registry`)
    Centralized registry managing lifecycle, initialization, health diagnostics,
    and teardown for every registered external infrastructure service.
    """
    _services: Dict[str, BaseInfrastructureManager] = {}

    @classmethod
    def register(cls, name: str, service: BaseInfrastructureManager) -> None:
        cls._services[name] = service
        logger.debug(f"Registered infrastructure service: '{name}'")

    @classmethod
    def get(cls, name: str) -> BaseInfrastructureManager:
        if name not in cls._services:
            raise KeyError(f"Infrastructure service '{name}' is not registered.")
        return cls._services[name]

    @classmethod
    def list_services(cls) -> List[str]:
        return list(cls._services.keys())

    @classmethod
    async def initialize_all(cls) -> Dict[str, bool]:
        """Initializes all registered infrastructure components (`6.10 Bootstrap Integration`)."""
        logger.info("Initializing all registered external infrastructure services...")
        results = {}
        for name, service in cls._services.items():
            logger.info(f" -> Initializing infrastructure service: '{name}'...")
            try:
                # Enforce 4s timeout for local DBs, but allow 15s for remote cloud APIs (`pinecone`, `groq`, `llm`)
                service_timeout = 15.0 if name in ("pinecone", "groq", "llm") else 4.0
                success = await asyncio.wait_for(service.initialize(), timeout=service_timeout)
                results[name] = success
                if success:
                    logger.info(f" ✔ Infrastructure service '{name}' initialized successfully.")
                else:
                    logger.warning(f" ⚠ Infrastructure service '{name}' initialized with warnings/stub mode.")
            except asyncio.TimeoutError:
                logger.warning(f" ⌛ Infrastructure service '{name}' connection timed out (>{service_timeout}s). Entering offline/stub mode.")
                service._is_initialized = True
                if hasattr(service, "stub_mode"):
                    service.stub_mode = True
                results[name] = False
            except Exception as exc:
                logger.error(f" ✖ Infrastructure service '{name}' initialization FAILED: {exc}")
                results[name] = False
        logger.info("=== Completed initializing all registered infrastructure services ===")
        return results

    @classmethod
    async def health_check_all(cls) -> Dict[str, Any]:
        """Performs health check on all registered services (`6.7 Health Integration`)."""
        diagnostics = {}
        all_healthy = True
        for name, service in cls._services.items():
            try:
                report = await service.health_check()
                diagnostics[name] = report
                if not report.get("healthy", False) and report.get("status") != "stubbed_local_dev":
                    all_healthy = False
            except Exception as exc:
                diagnostics[name] = {"healthy": False, "status": "error", "error": str(exc)}
                all_healthy = False
        return {"overall_status": "healthy" if all_healthy else "degraded", "services": diagnostics}

    @classmethod
    async def close_all(cls) -> None:
        """Closes all active external infrastructure connections."""
        logger.info("Closing all infrastructure connections...")
        for name, service in cls._services.items():
            try:
                await service.close()
                logger.info(f"Closed service '{name}'.")
            except Exception as exc:
                logger.error(f"Error while closing service '{name}': {exc}")
        cls._services.clear()
