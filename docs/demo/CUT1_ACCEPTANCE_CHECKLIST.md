# Cut 1 Demo Acceptance Checklist

Status: proposed with Issue #440. This is the executable human-review artifact
for the controlled Cut 1 demo; it is not a public-launch or production sign-off.

## Run contract

- Presenter: Meera; Raj is first backup; Myra is second backup.
- Input: one approved, versioned project knowledge pack and one approved script.
- Default framing: waist-up or mid-thigh; hands remain visible for meaningful
  gestures.
- Environment: local/key-free or explicitly approved controlled environment;
  paid providers remain disabled by default.
- Evidence: run ID, source checksum, script checksum, evaluator version,
  manifest checksum, captions, media artifact, and reviewer identity.

## Preflight

- [ ] Source pack is approved, versioned, checksum-bound, and tenant/project
      scoped.
- [ ] Script contains only supported claims and every material claim has a
      source/chunk reference.
- [ ] Presenter asset manifest records provenance, license/consent basis,
      checksum, and approval state.
- [ ] Model/provider/prompt/retriever/evaluator versions are recorded.
- [ ] No secrets, private source text, or provider payloads appear in logs or
      screenshots.

## Acceptance gates

| ID | Check | Pass condition | Result / evidence |
|---|---|---|---|
| C1-M01 | Eye contact | Camera-directed gaze covers at least 80% of speaking intervals; no accidental off-camera interval exceeds 2 seconds | |
| C1-M02 | Lip sync | P95 offset <=80 ms; no continuous segment >200 ms | |
| C1-M03 | Captions | >=98% approved-language word accuracy; no missing span >1 second | |
| C1-M04 | Grounding | 100% material claims are source-bound; zero unsupported golden-suite claims | |
| C1-M05 | Abstention | All unsupported prompts refuse or request clarification | |
| C1-M06 | Identity | No face, hair, clothing, background, or presenter-switch mismatch | |
| C1-M07 | Motion | No malformed limbs/fingers; no gesture repeated more than twice consecutively | |
| C1-M08 | Accessibility | Keyboard path, captions, >=4.5:1 normal-text contrast, reduced-motion behavior | |
| C1-M09 | Timing | P95 governed script/evaluation <=20 seconds; preview begins <=5 seconds after readiness | |
| C1-M10 | Reproducibility | Two runs have identical canonical script, bindings, evaluator version and manifest checksum | |

## Reviewer decision

- [ ] PASS: every P0 gate passes and all evidence is attached.
- [ ] CONDITIONAL: only a documented non-blocking issue remains with owner and
      expiry; no conditional result may be called Cut 1 accepted.
- [ ] FAIL: any P0 threshold, grounding, privacy, provenance, accessibility,
      or evidence-integrity condition fails.

Reviewer: ____________________  Date: ____________________

Evidence locations: ______________________________________________________

## Explicit non-claims

This checklist does not prove full-body walking, open-domain Q&A, public
availability, production reliability, legal approval, real-person likeness,
paid-provider readiness, or commercial launch. Those are later cut or
enterprise gates in `docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md`.
