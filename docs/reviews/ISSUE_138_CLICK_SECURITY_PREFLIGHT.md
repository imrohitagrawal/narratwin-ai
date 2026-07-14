# Issue 138 Click Security Remediation Preflight

## Status

Pre-implementation contract for issue `#138`. This document does not claim that
the dependency advisory is remediated, that required checks pass, or that issue
`#138` is complete.

## Intent

Remove vulnerable Click releases from the NarraTwin application, development,
container, and Semgrep execution environments without suppressing
`PYSEC-2026-2132` or silently skipping static analysis.

Semgrep `1.168.0` declares `click~=8.1.8`, while the advisory is fixed in Click
`8.3.3`. The remediation will isolate Semgrep from the application dependency
graph and use a scoped uv dependency override in the isolated tool project. The
override is acceptable only if the exact repository scan used by CI succeeds
with Semgrep `1.168.0` and Click `8.3.3`.

## Source Facts

- OSV `PYSEC-2026-2132` / `CVE-2026-7246` describes command injection through
  `click.edit()` and marks Click `8.3.3` as the first fixed version:
  `https://api.osv.dev/v1/vulns/PYSEC-2026-2132`.
- Semgrep `1.168.0` declares `click~=8.1.8`:
  `https://pypi.org/pypi/semgrep/1.168.0/json`.
- uv dependency overrides deliberately replace a transitive requirement and
  therefore require explicit compatibility proof:
  `https://docs.astral.sh/uv/reference/settings/#override-dependencies`.
- Before tracked changes, a local full repository scan completed with zero
  findings using Semgrep `1.168.0` after installing Click `8.3.3`. That probe is
  compatibility evidence only; the committed lockfiles and CI must reproduce it.

## Invariant-To-Test Matrix

| ID | Type | Required invariant | False-pass / failure mode | Positive evidence | Negative / mutation evidence | Gate | Owner | Preflight status |
|---|---|---|---|---|---|---|---|---|
| `SEC138-INV-001` | Security | Root application and development resolution contains Click `>=8.3.3` and contains no Semgrep package. | The root audit passes only because an advisory is ignored, while the runtime image still contains Click `8.1.8`. | Lock-contract unit test plus `uv run pip-audit`. | Mutate the root lock expectation to Click `8.1.8` or add Semgrep and prove the contract fails. | `make dependency-audit`; backend image scan | security/repo owner | planned |
| `SEC138-INV-002` | Tool isolation | Semgrep has an exact, separate project and lock using Semgrep `1.168.0` with Click `8.3.3`. | A floating tool install resolves the vulnerable Click release later. | Tool-project and lock-contract unit tests. | Remove the override, loosen the Semgrep pin, or change the locked Click version and prove the contract fails. | `uv lock --project tools/semgrep --check`; tool version check | security/repo owner | planned |
| `SEC138-INV-003` | SAST compatibility | The exact CI Semgrep command succeeds against all approved targets with the patched Click version. | Dependency audit becomes green by removing Semgrep, but SAST is skipped or scans fewer targets. | Full repository Semgrep execution and wrapper contract test. | Remove a required command token or target and prove the contract fails. | `make security` | security/repo owner | planned |
| `SEC138-INV-004` | No suppression | No `pip-audit` vulnerability ignore is added for `PYSEC-2026-2132`. | CI hides the advisory with `--ignore-vuln` and calls the result remediation. | Wrapper and Make target source assertions. | Add the advisory ignore token and prove the contract fails. | `make dependency-audit`; `make security` | security/repo owner | planned |
| `SEC138-INV-005` | Runtime compatibility | Uvicorn application startup, test tooling, and the backend image remain functional with the fixed Click release. | The override removes the advisory but breaks supported CLI or container behavior. | API/unit suites, backend Docker build, and version inventory. | Human review must reject a green audit without runtime/container proof. | `make ci`; `make container-scan` | platform/repo owner | planned |
| `SEC138-INV-006` | Governance | The change remains scoped to issue `#138` and makes no production, restore, RTO/RPO, `DUR-RESTORE-001`, or issue `#39` closure claim. | Security remediation is misrepresented as production readiness or restore evidence. | STATUS/TRACEABILITY review and PR guardrails. | Issue-closing and production-claim guardrails remain unchanged. | `python3 scripts/guardrails_check.py` | repo owner | planned |

## Human-Only Review Surfaces

| Surface | Automation gap | Owner | Required decision | Residual risk |
|---|---|---|---|---|
| Unsupported Semgrep dependency override | Semgrep upstream has not declared compatibility with Click `8.3.3`; repository tests cover only the committed invocation and rules. | security/repo owner | Accept the narrow tested override or require replacement/removal of Semgrep before merge. | Other unexercised Semgrep CLI paths may be incompatible. |
| Final PR approval and merge wording | CI cannot approve its own security exception boundary or inspect final squash wording in advance. | security/repo owner | Confirm reference-only issue wording and no production-readiness claim. | Issue `#138` remains open until the merged result is verified. |

## Implementation Plan

1. Isolate Semgrep in `tools/semgrep` with exact versions and a dedicated lock.
2. Remove Semgrep from the root dependency graph and regenerate the root lock.
3. Run the isolated, frozen Semgrep environment from the security wrapper.
4. Add contract tests that reject vulnerable locks, floating pins, advisory
   suppression, or a missing SAST invocation.
5. Update security, quality-gate, third-party, traceability, and status records.
6. Run focused tests, dependency/security gates, full quality, CI, and an
   independent adversarial review before requesting human approval.

## Stop Rule

Stop and reopen the contract before continuing if the exact Semgrep scan fails
with Click `8.3.3`, any other dependency requires a vulnerable Click release,
the root or tool audit reports another advisory, or the change needs a broad
security exception. Do not convert any such result into an ignored finding.
