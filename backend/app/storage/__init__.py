"""Shared durability helpers for optional file-backed service state."""

from .file_state import load_state, resolve_state_file, write_state
from .migrations import (
    AppliedMigrationRecord,
    MigrationContext,
    MigrationRegistryError,
    MigrationRevision,
    MigrationRunResult,
    MigrationRunner,
    MigrationStateError,
)
from .postgres_state import (
    AcidCasConflictError,
    AcidCasKernel,
    AcidCasStaleWriteError,
    ConsumerDeliveryRecord,
    OutboxEventWrite,
    StoredRecord,
    StoredOutboxEvent,
    TransactionCommitResult,
    TransactionWrite,
)

__all__ = [
    "AcidCasConflictError",
    "AcidCasKernel",
    "AcidCasStaleWriteError",
    "AppliedMigrationRecord",
    "ConsumerDeliveryRecord",
    "MigrationContext",
    "MigrationRegistryError",
    "MigrationRevision",
    "MigrationRunResult",
    "MigrationRunner",
    "MigrationStateError",
    "OutboxEventWrite",
    "StoredRecord",
    "StoredOutboxEvent",
    "TransactionCommitResult",
    "TransactionWrite",
    "load_state",
    "resolve_state_file",
    "write_state",
]
