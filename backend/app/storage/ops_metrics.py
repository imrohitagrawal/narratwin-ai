"""Shared CH-10 operations metrics contract and test-visible emitters."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Any, Literal

from prometheus_client import Counter, Gauge, Histogram

MetricKind = Literal["counter", "gauge", "histogram"]
MetricValue = int | float
MetricLabels = tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class OpsMetricContract:
    name: str
    kind: MetricKind
    description: str
    labels: tuple[str, ...]
    emission_boundary: str
    deferred_chunk: str | None = None


OPS_METRIC_CONTRACTS: dict[str, OpsMetricContract] = {
    "run_backlog": OpsMetricContract(
        name="narratwin_ops_run_backlog_gauge",
        kind="gauge",
        description="Durable run backlog by record state at the ACID/CAS contract boundary.",
        labels=("state",),
        emission_boundary="AcidCasKernel transaction commits that stage run rows.",
    ),
    "lease_state_count": OpsMetricContract(
        name="narratwin_ops_lease_state_count",
        kind="gauge",
        description="Lease inventory by active or stale state at the durable lease boundary.",
        labels=("state",),
        emission_boundary="AcidCasKernel lease acquire, heartbeat, and release operations.",
    ),
    "lease_staleness_seconds": OpsMetricContract(
        name="narratwin_ops_lease_staleness_seconds",
        kind="histogram",
        description="Observed lease staleness when a lease goes stale or is rejected as stale.",
        labels=("event",),
        emission_boundary="AcidCasKernel stale lease and stale writer rejection paths.",
    ),
    "lease_reacquire_total": OpsMetricContract(
        name="narratwin_ops_lease_reacquire_total",
        kind="counter",
        description="Lease reacquire events after expiry at the durable lease boundary.",
        labels=("resource_type",),
        emission_boundary="AcidCasKernel lease acquisition when a prior durable lease expired.",
    ),
    "idempotency_contract_drift_total": OpsMetricContract(
        name="narratwin_ops_idempotency_contract_drift_total",
        kind="counter",
        description="Idempotency payload-hash conflicts against committed durable state.",
        labels=("surface",),
        emission_boundary="AcidCasKernel operation start or commit payload-hash validation.",
    ),
    "idempotency_replay_total": OpsMetricContract(
        name="narratwin_ops_idempotency_replay_total",
        kind="counter",
        description="Idempotent durable operation replays against previously committed state.",
        labels=("state",),
        emission_boundary="AcidCasKernel replay paths for terminal and transient operation records.",
    ),
    "idempotency_terminal_replay_fail_total": OpsMetricContract(
        name="narratwin_ops_idempotency_terminal_replay_fail_total",
        kind="counter",
        description="Terminal replay mismatches against committed durable success or error payloads.",
        labels=("surface",),
        emission_boundary="AcidCasKernel terminal success or error replay conflict checks.",
    ),
    "stale_writer_reject_total": OpsMetricContract(
        name="narratwin_ops_stale_writer_reject_total",
        kind="counter",
        description="Stale owner or stale lease rejections on durable mutator paths.",
        labels=("surface",),
        emission_boundary="AcidCasKernel owner, lease, and recovery-epoch rejection paths.",
    ),
    "outbox_backlog_count": OpsMetricContract(
        name="narratwin_ops_outbox_backlog_count",
        kind="gauge",
        description="Durable outbox backlog by pending or delivering state.",
        labels=("state",),
        emission_boundary="AcidCasKernel outbox stage, acquire, retry, and complete transitions.",
    ),
    "outbox_age_seconds": OpsMetricContract(
        name="narratwin_ops_outbox_age_seconds",
        kind="histogram",
        description="Age of an outbox event when it is acquired, retried, or completed.",
        labels=("event_type", "phase"),
        emission_boundary="AcidCasKernel outbox dispatcher contract boundaries.",
    ),
    "outbox_redelivery_total": OpsMetricContract(
        name="narratwin_ops_outbox_redelivery_total",
        kind="counter",
        description="Outbox retry or redelivery attempts after an earlier dispatch attempt.",
        labels=("event_type",),
        emission_boundary="AcidCasKernel outbox retry scheduling.",
    ),
    "restore_attempts_total": OpsMetricContract(
        name="narratwin_ops_restore_attempts_total",
        kind="counter",
        description="Restore-adjacent local state load attempts and outcomes.",
        labels=("surface", "result"),
        emission_boundary="Shared file-state load_state restore-adjacent boundary only.",
        deferred_chunk="CH-14",
    ),
    "restore_duration_seconds": OpsMetricContract(
        name="narratwin_ops_restore_duration_seconds",
        kind="histogram",
        description="Restore-adjacent local state load durations by surface and outcome.",
        labels=("surface", "result"),
        emission_boundary="Shared file-state load_state restore-adjacent boundary only.",
        deferred_chunk="CH-14",
    ),
    "rollback_block_total": OpsMetricContract(
        name="narratwin_ops_rollback_block_total",
        kind="counter",
        description="Rollback-safety blocks at the reviewed rollback compatibility boundary.",
        labels=("reason",),
        emission_boundary="MigrationRunner reviewed rollback compatibility assertions.",
        deferred_chunk="CH-15",
    ),
}

_COUNTERS = {
    contract.name: Counter(contract.name, contract.description, contract.labels)
    for contract in OPS_METRIC_CONTRACTS.values()
    if contract.kind == "counter"
}
_GAUGES = {
    contract.name: Gauge(contract.name, contract.description, contract.labels)
    for contract in OPS_METRIC_CONTRACTS.values()
    if contract.kind == "gauge"
}
_HISTOGRAMS = {
    contract.name: Histogram(contract.name, contract.description, contract.labels)
    for contract in OPS_METRIC_CONTRACTS.values()
    if contract.kind == "histogram"
}

_LOCK = RLock()
_COUNTER_SNAPSHOT: dict[tuple[str, MetricLabels], float] = defaultdict(float)
_GAUGE_SNAPSHOT: dict[tuple[str, MetricLabels], float] = {}
_HISTOGRAM_OBSERVATIONS: dict[tuple[str, MetricLabels], list[float]] = defaultdict(list)


def counter_metric(metric_key: str, *, amount: float = 1.0, **labels: str) -> None:
    contract = OPS_METRIC_CONTRACTS[metric_key]
    label_values = _ordered_labels(contract, labels)
    _COUNTERS[contract.name].labels(*[value for _, value in label_values]).inc(amount)
    with _LOCK:
        _COUNTER_SNAPSHOT[(contract.name, label_values)] += amount


def gauge_metric(metric_key: str, value: MetricValue, **labels: str) -> None:
    contract = OPS_METRIC_CONTRACTS[metric_key]
    label_values = _ordered_labels(contract, labels)
    _GAUGES[contract.name].labels(*[label for _, label in label_values]).set(float(value))
    with _LOCK:
        _GAUGE_SNAPSHOT[(contract.name, label_values)] = float(value)


def histogram_metric(metric_key: str, value: MetricValue, **labels: str) -> None:
    contract = OPS_METRIC_CONTRACTS[metric_key]
    label_values = _ordered_labels(contract, labels)
    _HISTOGRAMS[contract.name].labels(*[label for _, label in label_values]).observe(float(value))
    with _LOCK:
        _HISTOGRAM_OBSERVATIONS[(contract.name, label_values)].append(float(value))


def timed_restore_load(*, surface: str) -> "_RestoreTiming":
    return _RestoreTiming(surface=surface)


def reset_ops_metric_snapshots() -> None:
    with _LOCK:
        _COUNTER_SNAPSHOT.clear()
        _GAUGE_SNAPSHOT.clear()
        _HISTOGRAM_OBSERVATIONS.clear()


def snapshot_ops_metrics() -> dict[str, Any]:
    with _LOCK:
        counters = {
            _snapshot_key(name, labels): value
            for (name, labels), value in sorted(_COUNTER_SNAPSHOT.items())
        }
        gauges = {
            _snapshot_key(name, labels): value
            for (name, labels), value in sorted(_GAUGE_SNAPSHOT.items())
        }
        histograms = {
            _snapshot_key(name, labels): tuple(values)
            for (name, labels), values in sorted(_HISTOGRAM_OBSERVATIONS.items())
        }
    return {
        "contracts": OPS_METRIC_CONTRACTS.copy(),
        "counters": counters,
        "gauges": gauges,
        "histograms": histograms,
    }


def record_restore_outcome(*, surface: str, result: str, duration_seconds: float) -> None:
    counter_metric("restore_attempts_total", surface=surface, result=result)
    histogram_metric("restore_duration_seconds", max(0.0, duration_seconds), surface=surface, result=result)


class _RestoreTiming:
    def __init__(self, *, surface: str) -> None:
        self.surface = surface
        self._started_at = monotonic()

    def observe(self, *, result: str) -> None:
        record_restore_outcome(
            surface=self.surface,
            result=result,
            duration_seconds=monotonic() - self._started_at,
        )


def _ordered_labels(contract: OpsMetricContract, labels: Mapping[str, str]) -> MetricLabels:
    missing = set(contract.labels) - set(labels)
    extra = set(labels) - set(contract.labels)
    if missing or extra:
        problems: list[str] = []
        if missing:
            problems.append(f"missing labels: {', '.join(sorted(missing))}")
        if extra:
            problems.append(f"unexpected labels: {', '.join(sorted(extra))}")
        raise ValueError(f"{contract.name} label mismatch ({'; '.join(problems)}).")
    return tuple((name, str(labels[name])) for name in contract.labels)


def _snapshot_key(name: str, labels: MetricLabels) -> str:
    if not labels:
        return name
    return name + "{" + ",".join(f"{key}={value}" for key, value in labels) + "}"
