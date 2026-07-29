# ADR 0042: Heartbeat 1 B browser, reopen, and privacy evidence

Status: Proposed for issue `#306` review under sole acceptance authority `#302`.

## Decision

Prove curation through a real browser, the Next same-origin rewrite, and the canonical backend without route fulfillment, request interception, or direct-backend success shortcuts.
Use one frontend and two sequential owned backend processes; stop and wait for backend 1, bind its exact snapshot digest, then start backend 2 with that same snapshot before reopening in a fresh browser context.
Submit the existing public and internal controlled fixtures exactly once each through permission-restricted runtime files, delete those files after both responses, and start tracing only afterward.
Publish snapshot, logs, DOM, screenshot, trace, and report evidence only after a recursive scanner proves zero controlled/canary matches across the authority encoding set and binds the exact run and commit.

## Consequences

The UI stores and renders bounded curation metadata only; internal content remains a source-less exclusion and cannot enter chunks, retrieval, logs, browser artifacts, or retained evidence.
Owner identities and accepted source/chunk bindings must agree before and after restart, while another local principal receives `403` through the frontend and sees no project actions.
This decision adds no backend contract, provider, deployment, spend, production, real-private-data, public-hosting, or Heartbeat 2 scope.
