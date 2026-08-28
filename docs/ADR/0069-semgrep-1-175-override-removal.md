# ADR 0069: Semgrep 1.175 Override Removal

Status: Proposed for Issue #460

Date: 2026-08-29

## Context

The isolated Semgrep tool environment was pinned to Semgrep `1.172.0` with
upstream Click `8.4.2` and one reviewed override from upstream MCP `1.23.3` to
fixed MCP `1.28.1`. That exception expired after `2026-08-28` and now fails the
mandatory dependency/security contract.

Official PyPI metadata checked on 2026-08-29 reports Semgrep `1.175.0` with
upstream requirements for Click `8.4.2`, MCP `1.29.0`, and PyJWT `2.13.0`.
Strict audits report no known vulnerabilities for the resolved root and
isolated inventories. The compatibility debt can therefore be removed rather
than renewed.

## Decision

Pin the isolated tool to exact Semgrep `1.175.0`, regenerate its Python 3.13
lock, and remove `override-dependencies` from the tool project. The executable
contract requires exact resolved identities:

- Semgrep `1.175.0`;
- Click `8.4.2`;
- MCP `1.29.0`;
- PyJWT `2.13.0`; and
- cryptography `50.0.0`.

The calendar exception is deleted. Any future override is rejected rather than
assigned a new expiry. Root and isolated audits remain separate and strict,
with no ignored advisory. The reviewed-input manifest is rebound only for the
tool manifest and generated lock changed here.

The existing local rules, exact target manifest, metrics-off invocation,
engine validation, nonempty clean scan, positive/clean canary, and backend
image exclusion remain unchanged.

Full-quality reproduction on the successor branch also exposed three
historical gates coupled to mutable current state. The bounded owner checkpoint
`5456985567`, body SHA-256
`7249ff4694fbf333f826147737e4e3e45e33cef045a6e507da029fbdd79da42f`,
authorizes only four additional convergence paths. Issue `#16` now validates
its immutable accepted snapshot on successors while retaining live route checks
on its exact original branch. The Issue `#427` prerequisite reads its frozen
base, and the Issue `#434` historical route test isolates its original charge
from successor edits. The original 17-path preflight remains byte-immutable;
the combined reviewed route is exactly 21 paths with a 2,000-line cap.

Hosted security then reproduced a topology-specific full-history failure: the
exact Issue `#460` range was clean, but checkout fetched the remote Issue `#459`
branch and Gitleaks rediscovered three immutable SHA-256 governance literals.
Checkpoint `5457578336`, body SHA-256
`82773778e0a791dffcf4f6f27cb265df6013f2a79ae107d484d1db10c8697368`,
authorizes four more paths only. The final route is exactly 25 paths with a
2,600-line cap. Each suppression binds the exact commit, path, rule, line,
frozen API-contract digest, and frozen Issue `#459` head. A representative real
secret must still be detected before the unchanged full-history scan runs.

## Rejected alternatives

- Renew MCP `1.28.1`: unnecessary because reviewed upstream metadata now pins a
  newer fixed MCP release.
- Broaden the Semgrep pin: non-deterministic and inconsistent with the frozen
  tooling contract.
- Ignore audit findings or expiry: weakens a mandatory security gate.
- Move Semgrep into the root/runtime graph: violates tool isolation and would
  expand the application attack and dependency surface.
- Remove SAST: loses an established security boundary and canary.
- Skip full Git history or use a broad Gitleaks exclusion: would conceal real
  secrets outside the current range and cannot distinguish the reviewed hashes.

## Consequences

The mandatory security wrapper no longer depends on a calendar exception.
Semgrep and MCP remain security tooling only; no MCP server is started or
exposed. This decision changes no application dependency, product behavior,
provider, credential, infrastructure, deployment, release, or production
posture. Any Semgrep version, lock, rule, target, invocation, canary, or reviewed
input change still requires a new reviewed route and complete security parity.

## Verification

- focused RED/GREEN dependency-security contract;
- generated-lock check and exact identity assertions;
- strict root and isolated `pip-audit` runs;
- reviewed-input hash validation;
- Semgrep engine validation, full target scan, and positive/clean canary;
- secrets, container, Stage 8, complete quality, CI, hosted checks; and
- independent exact-head security and technical review.

These checks prove only the isolated tooling correction. They do not prove
release, deployment, public availability, commercial readiness, or production
readiness.
