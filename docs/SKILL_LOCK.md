# Skill Lock

## Purpose

This file records external skills and tooling that Codex may use for NarraTwin AI.

A skill is not active until its source, version pin, license status, install command, and stage are recorded here.

## Lock rules

- Do not install every skill at once.
- Do not activate a skill outside its approved stage.
- Do not use a skill with unclear license or install behavior for implementation.
- Do not allow a skill to override NarraTwin AI PRD, ADRs, security, privacy, consent, or quality gates.
- If a skill changes files, hooks, network behavior, telemetry, or CI behavior, record that before use.
- Exact commit SHA or release tag must be recorded before a skill is used for implementation.

## Stage 0 approved planning sources

| Skill/tool | Source URL | Pin or version | License status | Purpose | Active stage | Activation status |
|---|---|---|---|---|---|---|
| PM Skills | https://github.com/phuryn/pm-skills | Pin required before activation | Review required before install | Product strategy, PRD, roadmap, metrics, PRD red-team review | Stage 0 and Stage 1 | Blocked until pin and license are recorded |
| GitHub Spec Kit | https://github.com/github/spec-kit | v0.11.9 from approved plan | Review required before install | Specification workflow, constitution, plan, tasks, implementation control | Stage 0 through Stage 2 | Approved only after local install verification |
| Addy Osmani Agent Skills | https://github.com/addyosmani/agent-skills | Pin required before activation | Review required before vendoring | Spec discipline, planning, TDD, code review, security, CI/CD, shipping | Stage 0 through Stage 8 | Blocked until pin and license are recorded |
| Agent Skills standard | https://github.com/agentskills/agentskills | Pin required before activation | Review required before vendoring | Portable skill-folder structure and skill metadata discipline | Stage 0 | Blocked until pin and license are recorded |

## Later-stage candidate sources

| Skill/tool | Source URL | Pin or version | License status | Purpose | Active stage | Activation status |
|---|---|---|---|---|---|---|
| Wednesday AI Agent Skills | https://github.com/wednesday-solutions/ai-agent-skills | Pin required before activation | Review required before install | Repo-aware codebase structure and coding guardrails after meaningful code exists | Stage 2 through Stage 8 | Not active in Stage 0 |
| UI/UX Pro Max | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | Pin required before activation | Review required before install | UI polish, demo preview quality, accessibility, visual design | Stage 7 | Not active in Stage 0 |

## Stage 0 activation decision

For the current Stage 0 remediation, no external skill is being executed by this repository change. The purpose of this file is to make the lock contract explicit before later Codex sessions install or activate any skill.

## Update requirement

When Codex installs, activates, vendors, or relies on any external skill, update this file with:

- exact source URL
- commit SHA, release tag, or immutable package version
- license decision
- install command used
- files changed by the installer
- stage of use
- reason for use
- reviewer decision
