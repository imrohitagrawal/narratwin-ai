# ADR 0085: Documentation navigation and lifecycle discovery

## Status

Proposed in Issue537 / draft PR536. No product or acceptance-policy effect.

## Context

Existing product/governance rules, templates and historical evidence occupy different valid locations. A newcomer must discover the owner and intended use without treating duplicated prose or a work folder as new authority. Native GitHub templates have tool-defined locations.

## Decision

Use one DocumentationNavigationV1 catalog for public source roles, maintainer roles, update triggers, template references and declared implementation-area documentation routes. Generate document, template and ADR indexes; preserve original paths and full-filename ADR identities. A concise contributor guide routes discovery, design, issue, implementation, PR and closeout; existing policy remains canonical.

Use tracked public files, safe file reads, supported structural Markdown links, finite configurable Git timeout, source-declared ADR status and positive/negative integrity checks. Native forms use JSON-compatible YAML so structural validation needs no new dependency.

## Consequences

One catalog is maintained; generated views fail on drift. Full source semantics, complete discussion capture, capability-backed README, Mermaid/ADR authority lifecycle, changed-code impact enforcement and production readiness are not proved. Legacy collisions and source ambiguity remain explicit. Existing ARCHITECTURE, AGENTS, anchored playbook, original recovered sources and PR534 subject remain unchanged.

## Alternatives and migration

Moving all files would break historical bindings; duplicate template copies would drift; a new stacked governance base would require unrelated routing changes. Use prospective535 scope amendments and link537 as its own stable work record. No original source is deleted or renamed.

## References

- [Documentation guide](../DOCUMENTATION_GUIDE.md)
- [Reviewed plan](../work/documentation-architecture/PLAN.md)
- [Existing architecture index](../ARCHITECTURE.md)
- [Current status](../STATUS.md)
