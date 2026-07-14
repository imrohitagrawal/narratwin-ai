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
- An unreviewed local probe indicated that the committed scan shape can run with
  Semgrep `1.168.0` and Click `8.3.3`. The probe is not acceptance evidence. Only
  the frozen tool lock, recorded command output, CI result, and reviewer decision
  produced by this change may be used as compatibility evidence.

## Invariant-To-Test Matrix

| ID | Type | Required invariant | False-pass / failure mode | Positive evidence | Negative / mutation evidence | Gate | Owner | Preflight status |
|---|---|---|---|---|---|---|---|---|
| `SEC138-INV-001` | Security | Root application and development resolution contains Click `>=8.3.3`, contains no Semgrep package, and defines no dependency override. | The root audit passes only because an advisory is ignored, while the runtime image still contains Click `8.1.8`. | Lock-contract unit test plus fail-closed `uv run pip-audit`. | Mutate the root lock to Click `8.1.8`, add Semgrep, or add a root override and prove the contract fails. | `make dependency-audit`; backend image inventory | security/repo owner | planned |
| `SEC138-INV-002` | Tool isolation | Semgrep has a separate frozen project and lock with exact Semgrep `1.168.0` and exactly one override, `click==8.3.3`; its environment path is distinct from the root environment. | A floating/shared tool install resolves vulnerable Click or changes root packages. | Tool-project, lock, and environment-path contract tests. | Remove or broaden the override, loosen the Semgrep pin, or reuse the root environment and prove the contract fails. | `uv lock --project tools/semgrep --check`; isolated tool version check | security/repo owner | planned |
| `SEC138-INV-003` | SAST compatibility | The exact CI Semgrep command succeeds with `--error`, `--metrics=off`, local `semgrep.yml`, and every path in one canonical target manifest. | Dependency audit becomes green by removing Semgrep, but SAST is skipped or scans fewer targets. | Full repository Semgrep execution and exact manifest/wrapper contract test. | Remove any target or required flag, change the config, or delete the command and prove the contract fails. | `make security` | security/repo owner | planned |
| `SEC138-INV-004` | Root audit | Root dependency audit runs fail-closed with no advisory aliases, ignore flags, alternate audit config, output filtering, or swallowed exit status. | CI hides the advisory with an alias ignore, deletes the audit, or converts failure to success. | Wrapper/Make source assertions and successful root audit. | Add `PYSEC-2026-2132`, `CVE-2026-7246`, `GHSA-47fr-3ffg-hgmw`, an ignore/config bypass, `|| true`, or remove the audit and prove the contract fails. | `make dependency-audit`; `make security` | security/repo owner | planned |
| `SEC138-INV-005` | Tool audit | The exported frozen Semgrep lock is audited fail-closed with zero ignores before the SAST command runs. | Root audit is green because the vulnerable scanner graph moved out of scope. | Tool-lock export plus `pip-audit` requirements audit. | Introduce any vulnerable tool dependency, suppress an alias, remove the tool audit, or swallow its exit code and prove the contract fails. | `make security` | security/repo owner | planned |
| `SEC138-INV-006` | Runtime compatibility | Uvicorn startup/CLI, Locust CLI, and the backend image remain functional; the built image explicitly reports Click `>=8.3.3` and no Semgrep. | The root change removes the advisory but breaks a Click consumer or leaves a vulnerable runtime image. | API/unit suites, Uvicorn/Locust smoke, Docker build, and explicit image package assertion. | A vulnerable Click or Semgrep entry in an image inventory must fail independently of the image scanner. | `make ci`; `make container-scan` | platform/repo owner | planned |
| `SEC138-INV-007` | Compatibility exception | The tool-only override is explicitly narrow, expires on `2026-08-13`, and is revisited on any Semgrep version/lock/invocation change or the first upstream release supporting fixed Click. | An unsupported override silently becomes permanent or is generalized to other Semgrep CLI paths. | Expiry/shape contract test and tracked upstream-removal issue. | Expired date or changed tool inputs fail until the preflight and reviewer decision are renewed. | focused contract test; human review | security/repo owner | planned |
| `SEC138-INV-008` | Governance | The change remains scoped to issue `#138` and makes no production, restore, RTO/RPO, `DUR-RESTORE-001`, or issue `#39` closure claim. | Security remediation is misrepresented as production readiness or restore evidence. | STATUS/TRACEABILITY review and PR guardrails. | Issue-closing and production-claim guardrails remain unchanged. | `python3 scripts/guardrails_check.py` | repo owner | planned |

## Human-Only Review Surfaces

| Surface | Automation gap | Owner | Required decision | Residual risk |
|---|---|---|---|---|
| Unsupported Semgrep dependency override | Semgrep upstream has not declared compatibility with Click `8.3.3`; repository tests cover only the committed invocation and rules. | security/repo owner | Before merge, record a dated decision accepting only the committed invocation through `2026-08-13`; revisit on any Semgrep version, lock, rules, or invocation change and remove the override when upstream supports fixed Click. | Other unexercised Semgrep CLI paths may be incompatible and are not approved. |
| Final PR approval and merge wording | CI cannot approve its own security exception boundary or inspect final squash wording in advance. | security/repo owner | Confirm reference-only issue wording and no production-readiness claim. | Issue `#138` remains open until the merged result is verified. |

## Implementation Plan

1. Isolate Semgrep in `tools/semgrep` with exact versions and a dedicated lock.
2. Remove Semgrep from the root dependency graph and regenerate the root lock.
3. Add one canonical Semgrep target manifest and run the isolated, frozen
   environment from the security wrapper.
4. Audit both the root and exported tool locks fail-closed with zero ignores.
5. Add contract tests that reject vulnerable locks, floating pins, broad
   overrides, advisory aliases/suppression, swallowed exits, target drift, or a
   missing audit/SAST invocation.
6. Add Uvicorn/Locust smoke and explicit backend-image package inventory proof.
7. Update security, quality-gate, third-party, traceability, and status records.
8. Open a dated upstream-compatibility follow-up, then run focused tests,
   dependency/security gates, full quality, CI, and an
   independent adversarial review before requesting human approval.

## Stop Rule

Stop and reopen the contract before continuing if the exact Semgrep scan fails
with Click `8.3.3`, any other dependency requires a vulnerable Click release,
either audit reports an advisory, the tool environment is not isolated, a
required target or consumer smoke is absent, or the change needs a broad
security exception. Do not convert any such result into an ignored finding.
