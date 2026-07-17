# File: app/repositories/postgres/__init__.py
"""
PostgreSQL Repository Layer (`7.2 PostgreSQL Repositories`).
Manages structured relational data (Users, Profiles, Sessions, Sources, Evaluation, Configs).
"""
from app.repositories.postgres.user_repository import UserRepository, UserTable
from app.repositories.postgres.profile_repository import UserProfileRepository, UserProfileTable
from app.repositories.postgres.session_repository import SessionRepository, SessionTable
from app.repositories.postgres.knowledge_source_repository import KnowledgeSourceRepository, KnowledgeSourceTable
from app.repositories.postgres.evaluation_repository import EvaluationRepository, EvaluationResultTable
from app.repositories.postgres.configuration_repository import ConfigurationRepository, ConfigurationItemTable
from app.repositories.postgres.document_repository import DocumentRepository, DocumentTable
from app.repositories.postgres.document_file_repository import DocumentFileRepository, DocumentFileTable

__all__ = [
    "UserRepository",
    "UserTable",
    "UserProfileRepository",
    "UserProfileTable",
    "SessionRepository",
    "SessionTable",
    "KnowledgeSourceRepository",
    "KnowledgeSourceTable",
    "EvaluationRepository",
    "EvaluationResultTable",
    "ConfigurationRepository",
    "ConfigurationItemTable",
    "DocumentRepository",
    "DocumentTable",
    "DocumentFileRepository",
    "DocumentFileTable",
]
