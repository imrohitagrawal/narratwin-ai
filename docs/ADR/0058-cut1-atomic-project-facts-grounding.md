# ADR 0058: Cut 1 atomic project-facts grounding

- Status: proposed in Issue #421; effective only after reviewed merge
- Date: 2026-08-12
- Decision owner: Rohit Agrawal / StackClimb
- Contract-identity dependency only: ADR 0055 supplies canonical claim bytes but
  is never facts/source evidence; all factual support is pinned to accepted
  commit `a868137fab607ae75d4b272301e9fc52b898e15c` and the independent OWNER span
  below.

## Context

The accepted Cut 1 narration contains eighteen visible claims per presenter. The
ordinary Stage 4 evaluator correctly requires each visible claim to occur
directly in its cited retrieved chunk. Genuine accepted repository sources do
not repeat those eighteen narration sentences, so the ordinary evaluator
returns eighteen unsupported claims and no accepted script. Copying the
narration into an uploaded source or generating narration-shaped paraphrases
would make the support circular.

Issue #421 needs a narrow route that preserves direct support everywhere else
while proving Cut 1 claims from independently stated atomic propositions and
their immutable source spans.

## Decision

`docs/governance/cut1-project-facts-v1.json` is the owner-reviewed policy asset.
Its complete byte-level SHA-256 is
`7fe8f85c9d803f7c95f6c0122fda784310134778e28c892d43eefc8d4c27917c`;
the verifier pins that digest before parsing any contract field.
It contains:

- independent, concise proposition statements;
- exact accepted repository source paths/revision plus the immutable OWNER
  comment URL/revision and only its independent 350-byte brand/ownership span;
- full-source byte counts and SHA-256 values;
- exact byte ranges, span bytes, byte counts, and SHA-256 values;
- eighteen ordered claim IDs with exact presenter-specific claim hashes; and
- a code-owned predicate checklist and the complete proposition set required
  for each claim.

The asset is not ordinary generated knowledge and does not copy canonical
narration sentences. Its safe Stage 4 upload projection contains only
proposition IDs and independent statements. Hashes and source-span bytes remain
in the repository policy asset so the ordinary untrusted-upload secret detector
does not need to be weakened.

`backend.app.cut1_grounding` is an exact-policy verifier. It:

1. verifies the pinned complete asset digest, then strict-parses bounded JSON
   with duplicate and unknown fields rejected;
2. requires the frozen schema, policy, source allowlist, and accepted revision;
3. loads each repository source from current bytes only when its SHA-256
   matches, otherwise from the pinned local Git object at the accepted revision;
4. binds the pre-existing OWNER record by exact URL, comment revision, complete
   body byte count/SHA-256, and the one permitted non-narration span; later
   narration bytes in that comment are not stored or used;
5. independently verifies every repository source and exact span byte range;
6. requires all propositions to be used and every code-owned required predicate
   to be covered by a verified proposition;
7. first runs the unchanged ordinary evaluator and permits the special route
   only when its sole failure is direct-substring absence for all eighteen
   structurally valid claims;
8. identifies the exact presenter by recomputing the complete ordered canonical
   claim-hash set rather than trusting the facts asset;
9. requires every claim to cite a project-owned retrieved chunk from the exact
   canonical project-facts projection; and
10. emits recomputed predicate/proposition IDs and an evidence checksum into each persisted
   claim support.

The Stage 4 service selects this verifier only for the exact
`CUT1_ATOMIC_FACTS_V1` style. That selection is not proof: any caller-provided
proposition metadata is rejected for every style at the Stage 4 generation
boundary, and all source, claim, mapping, scope, and
retrieval evidence is recomputed. All other styles continue to use the existing
direct-support evaluator.

Evaluation lineage includes a conditional `groundingEvidence` object only for
this policy. It binds each claim ID, every proposition ID, each proposition
evidence checksum, the policy version, and an aggregate checksum. Existing v2
lineage bytes and their golden digest remain unchanged.

Restore and replay dispatch by the persisted evaluation policy and require the
exact Cut 1 style. The same canonical verifier reruns against the pinned source
revision and current stored project graph. Missing Git objects, modified policy
assets, stale facts projections, cross-project chunks, incomplete mappings, or
checksum drift make the run unavailable rather than trusted.

## Alternatives rejected

- **Narration as an uploaded source:** circular self-grounding.
- **Narration-derived source paraphrases:** source stuffing under a different
  wording.
- **Fuzzy overlap or semantic similarity:** nondeterministic and over-broad.
- **Model-as-judge support:** caller/model confidence cannot establish source
  truth.
- **Hard-coded success or fixture branches:** no independent evidence.
- **Replace ordinary direct support:** weakens all Stage 4 projects.
- **Directly construct runs, approvals, or receipts:** bypasses persistence and
  restore contracts.

## Security and privacy consequences

- Facts, uploaded content, generated text, and persisted state remain untrusted.
- Paths are an exact repository allowlist; no arbitrary filesystem read exists.
- Git is invoked without a shell, at a fixed revision and allowlisted path, with
  a timeout; command output is never logged.
- Errors are bounded and disclose no narration, source spans, private paths, or
  subprocess details.
- No network, telemetry, provider, authentication, or billing behavior is added.
- No provider call is authorized from this repair branch.

## Limits

This policy proves deterministic proposition/source binding, not spoken-word
accuracy, pronunciation, voice quality, legal clearance, release readiness, or
production durability. It is intentionally specific to the owner-reviewed Cut
1 narration and accepted revision. Other scripts and projects retain ordinary
direct support unless separately governed.

Issue #368 remains open. Release, deployment, distribution, and public or
commercial use remain No-Go.
