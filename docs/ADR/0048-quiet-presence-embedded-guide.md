# ADR 0048: Quiet Presence Embedded Guide Boundary

## Status

Accepted for Issue #358 local/mock `/demo`; no deployment or production authority.

## Context

NarraTwin must remain visibly subordinate to the project it explains. The first
browser-playable cut demonstrates that relationship inside a simulated Northwind
workspace while preserving a future plug-and-play host integration path. The
selected Quiet Presence concept uses a bottom Guide Ribbon and an optional dark
Focus Stage. It must not depend on, inspect, or mutate an embedding product's DOM.

## Decision

Keep `/demo` as a local/mock product surface with two future host modes:

- **Reserved mode:** the host reserves the shared `--guide-height` region so its
  content remains visible above the Guide Ribbon.
- **Overlay mode:** a future commercial host adapter may overlay the ribbon when
  the host explicitly opts in and supplies its own safe-area/layout contract.

The current simulated host uses reserved mode. One bounded responsive height token
governs host padding, sidebar extent, and ribbon height; the collapsed value is
60 px and is the default on short desktop viewports. Mobile uses a full-screen
guide with explicit Back and Minimize return paths plus a host-visible launcher.

Focus Stage is a genuine modal: the background is inert, focus stays within the
dialog, Escape closes it, and focus returns to the originating Focus control.
The presenter is an OpenAI-generated, photorealistic fictional adult Indian woman
created without a real-person reference and disclosed as a synthetic still image.
It is not intended to depict or endorse a real person. Evidence and explanation
remain primary; the preview is not a registered render identity and implies no
playback, animation, real media, cloned identity, or provider-runtime activation.

Successful UI state requires exact ordered Stage 4 source/evaluation mappings,
matching Stage 6 and Stage 7 lineage, approved local/mock provider identities and
modes, confirmed consent, no external egress, no real-video capability, and no
cloned identity. Labels come from validated responses. Before that boundary passes,
the host is a **Simulated host context**; only afterward is it a **Verified project
source**. Q&A and governed web search remain visibly disabled/planned.

## Host-adapter boundary

A future commercial adapter may provide project identity, host mode, launcher
placement, and the reserved-height contract through a versioned integration API.
It may not grant NarraTwin general DOM access or allow selector-based host coupling.
Cross-origin embedding, authentication, tenant isolation, events, consent, web
search, provider enablement, deployment, and billing require separate decisions.

## Alternatives rejected

- A floating presenter over arbitrary host content: rejected because it obscures
  the product being explained and creates collision/accessibility risk.
- Direct host selector/DOM inspection: rejected because it is brittle, invasive,
  and unsuitable for commercial plug-and-play isolation.
- Always-expanded guide on laptops: rejected because it reduces the host to a
  backdrop instead of the primary working surface.
- Fake Pause, Q&A, web search, or video controls: rejected because they overstate
  the implemented local/mock capability.

## Consequences

- The Cut 1 UI foundation demonstrates a truthful Stage 4→6→7 local/mock walkthrough without
  changing backend/API contracts, root UI, dependencies, or provider posture.
- A commercial host adapter remains possible without treating this simulated
  workspace as production integration evidence.
- Deployment, public availability, real avatar media, internet-enabled answers,
  and production readiness remain separate future gates.
