# PRD: NarraTwin AI

## Problem

Project creators often explain technical work using English-only README files and demo videos. Recruiters, hiring managers, non-English audiences, and non-technical stakeholders may not get the right level of explanation.

## Goal

Create a platform that transforms approved project knowledge into multilingual, audience-aware avatar walkthroughs and Q&A.

## MVP scope

- create/select project
- upload markdown/text project knowledge
- ingest/chunk/store documents
- retrieve relevant context
- generate grounded walkthrough script
- select audience, language, depth, and style
- evaluate unsupported claims
- store outputs
- display results in UI

## Non-goals for MVP

- full realtime avatar conversation
- paid provider dependency
- voice cloning
- face cloning
- production-grade video rendering quality
- commercial avatar marketplace

## Personas

- Recruiter: wants a 60-second project summary.
- Hiring Manager: wants business impact, ownership, trade-offs.
- Engineer: wants architecture and implementation depth.
- Global Viewer: wants localized language explanation.
- Project Creator: wants reusable project storytelling.

## Acceptance criteria for first slice

- User can create a project.
- User can upload markdown/text knowledge.
- System chunks and stores documents.
- User can request a walkthrough script.
- Script is grounded in uploaded content.
- Unsupported claims are flagged/refused.
- Output is visible in UI and stored.
- Tests pass without real paid provider keys.
