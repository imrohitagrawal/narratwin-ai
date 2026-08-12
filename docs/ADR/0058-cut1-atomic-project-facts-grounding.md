# ADR 0058: Cut 1 atomic project-facts grounding

- Status: proposed in Issue #421; effective only after reviewed merge
- Date: 2026-08-12
- Decision owner: Rohit Agrawal / StackClimb
- Contract-identity dependency only: ADR 0055 and OWNER comment `5263752038`
  supply canonical claim bytes but are never self-grounding evidence. Factual
  support is pinned to accepted commit
  `a868137fab607ae75d4b272301e9fc52b898e15c` or exact first-party
  `OWNER_ASSERTED` spans. Owner assertions are not externally corroborated.

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
`f9d443bb42ff00028c725e007f5fd52a06cc1863cac44c0bb2214ace79ac0f6e`;
the verifier pins that digest before parsing any contract field.
It contains:

- concise proposition statements classified as `REPOSITORY_SOURCE` or
  `OWNER_ASSERTED`; repository means narration-independent checked-in evidence,
  not external corroboration;
- exact accepted repository source paths/revision plus two immutable OWNER
  comment URL/revisions and only their four code-owned factual spans;
- full-source byte counts and SHA-256 values;
- exact byte ranges, span bytes, byte counts, and SHA-256 values;
- eighteen ordered claim IDs with exact presenter-specific claim hashes; and
- a code-owned predicate checklist and the complete proposition set required
  for each claim.

The asset is not ordinary generated knowledge and does not copy the narration
as a whole. Three exact narration claims are separately authorized first-party
facts; their Stage 4 projection is visibly tagged `OWNER_ASSERTED`. Other
propositions remain `REPOSITORY_SOURCE`. Hashes and source-span bytes remain in
the repository policy asset so the ordinary untrusted-upload secret detector
does not need to be weakened.

`backend.app.cut1_grounding` is an exact-policy verifier. It:

1. verifies the pinned complete asset digest, then strict-parses bounded JSON
   with duplicate and unknown fields rejected;
2. requires the frozen schema, policy, source allowlist, and accepted revision;
3. loads each repository source from current bytes only when its SHA-256
   matches, otherwise from the pinned local Git object at the accepted revision;
4. records both OWNER records' exact URL, comment revision, complete body byte
   count/SHA-256, classification, and code-pins all four permitted factual
   spans' offset, length, digest, and bytes; runtime does not fetch comments;
5. independently verifies every repository source and exact span byte range;
6. requires all propositions to be used and every code-owned required predicate
   to be covered by a verified proposition;
7. first runs the unchanged ordinary evaluator and requires exactly the two
   literal OWNER claims to have generic direct support while the other sixteen
   remain unsupported only for direct-substring absence;
8. accepts only Meera for Cut 1 by recomputing her complete ordered canonical
   claim-hash set rather than trusting the facts asset or caller;
9. requires every claim to cite a project-owned retrieved chunk from the exact
   canonical project-facts projection; and
10. emits recomputed predicate/proposition IDs, source classifications, and an
    evidence checksum into each persisted claim support.

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
1 Meera narration at 261 words, 1,904 UTF-8 bytes and SHA-256
`3edffc6169460546ae0bdee867fdeaf3c0ae383535e2976e0333f39c03ff614e`.
Other scripts and projects retain ordinary direct support unless separately
governed.

Issue #368 remains open. Release, deployment, distribution, and public or
commercial use remain No-Go.
