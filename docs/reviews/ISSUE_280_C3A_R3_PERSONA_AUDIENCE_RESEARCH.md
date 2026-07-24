# Issue #280 Persona, Audience, And Depth Research

## Research Basis

Sources verified on 2026-07-24:

- Nielsen Norman Group, personas and jobs-to-be-done:
  https://www.nngroup.com/articles/personas-jobs-be-done/
- Nielsen Norman Group, concise/scannable/objective web writing:
  https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/
- GOV.UK Service Manual, learning about users and needs:
  https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs
- ONS Service Manual, user personas:
  https://service-manual.ons.gov.uk/content/writing-for-users/user-personas
- Digital.gov plain language topic:
  https://digital.gov/topics/plain-language
- Google PAIR, mental models:
  https://pair.withgoogle.com/chapter/mental-models/
- Microsoft HAX, Guidelines for Human-AI Interaction:
  https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/
- W3C WAI WCAG language of page:
  https://w3c.github.io/wcag/understanding/language-of-page
- W3C WAI WCAG language of parts:
  https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts
- W3C Internationalization Best Practices:
  https://www.w3.org/TR/international-specs/

Synthesis:

- Personas must represent researched user goals, needs, context, pain points,
  knowledge level, and tasks; they are not demographic stereotypes.
- User needs start from what people are trying to do and the outcome they need.
- Plain language means writing for the actual audience so they can understand
  and use the content, not flattening all users to a beginner level.
- Web content should be concise, scannable, and objective.
- AI experiences need expectation-setting, explainability, control, and graceful
  repair paths.
- Multilingual output needs visible language, language-of-parts, direction, and
  script handling for assistive technology and international users.

## Invariant

Audience changes framing, emphasis, vocabulary, explanation order, and
source-supported examples. Audience does not change underlying facts, add
uncited claims, remove required evidence, or alter citation/context/claim-support
bindings.

Depth changes amount and structure. It does not alter evidence boundaries.

## Audience Rows

| audienceMode | researchBasis | jobToBeDone | decisionContext | knowledgeLevel | preferredEvidence | toneBoundary | depthBehavior | translationRisk | accessibilityRisk | goldenRules | evilSet | sourceBindingRule | testRows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Recruiter | NN/g personas; GOV.UK needs; Digital.gov plain language audience guidance | Quickly judge role fit and candidate signal from a project walkthrough. | Screening or shortlisting. | Medium technical literacy, limited project context. | Clear role signal, cited outcomes, concise examples. | Professional and specific; no inflated candidate claims. | Concise: strongest role signal only. Standard: role fit plus project clarity. Deep: source-supported tradeoffs and evidence that show scope and judgment. | Hiring terms may not map cleanly across cultures. | Must expose citations and selected audience/depth. | Emphasize role fit, project clarity, candidate signal. | Prefix-only adaptation, unsupported hiring claims, stereotypes. | Every role-fit claim must bind to cited source text or explicit project evidence. | R280-AUDIENCE-RECRUITER, R280-AUDIENCE-DEPTH-001 |
| Hiring manager | GOV.UK needs; ONS knowledge/task split; Microsoft HAX expectation setting | Decide whether the project evidence supports delivery confidence and evaluation relevance. | Team evaluation and risk review. | Medium to high product/technical context. | Risks, constraints, delivery proof, evaluation results. | Direct and sober; no production-readiness overclaim. | Concise: decision signal and top risk. Standard: delivery confidence with caveats. Deep: source-supported risks, mitigations, pros/cons. | Risk terms can be softened or exaggerated in translation. | Caveats must remain visible after translation. | Emphasize decision usefulness, risk, delivery confidence, evaluation relevance. | Removing source-backed caveats, uncited team-fit claims. | Risk and confidence claims require citations/contextRefs/claimSupports. | R280-AUDIENCE-HIRING, R280-DEPTH-CAVEAT |
| Engineer | ONS technical users; NN/g domain-expert writing; API/interface contract | Understand architecture, implementation constraints, interfaces, reliability, and tradeoffs. | Technical review or handoff. | High technical literacy. | Interfaces, invariants, tests, failure modes, tradeoffs. | Precise, implementation-aware, no vague slogans. | Concise: architecture thesis. Standard: interfaces and constraints. Deep: source-supported edge cases, tradeoffs, caveats, pros/cons. | Technical terms and acronyms may be mistranslated. | Code-like terms and direction/script metadata must be protected. | Emphasize architecture, constraints, interfaces, reliability, tradeoffs. | Synonym-only adaptation, unsupported architecture claims. | Technical claims must bind to source spans and maintain citation order. | R280-AUDIENCE-ENGINEER, R280-GLOSSARY-ACRONYM |
| Product leader | GOV.UK outcome framing; Google PAIR mental models; Digital.gov plain language | Decide whether the project communicates user value, adoption path, outcomes, and roadmap-safe risk. | Product strategy review. | Medium product literacy, variable technical depth. | User value, adoption risk, outcome evidence, limitations. | Outcome-focused without roadmap or market overclaim. | Concise: value and limitation. Standard: outcome narrative. Deep: source-supported tradeoffs, caveats, implications. | Product idioms can be culture-specific. | Avoid local-only idioms and keep limitations visible. | Emphasize user value, adoption, outcomes, risks, roadmap-safe framing. | Unsupported adoption claims, private strategy inference. | Outcome claims require cited project facts or explicit public contract. | R280-AUDIENCE-PRODUCT, R280-CONVERSATION-UX |
| Customer | GOV.UK user needs; Digital.gov plain language; Microsoft HAX repair paths | Understand workflow value, trust boundaries, limitations, and expected benefit. | Evaluating whether the tool solves a practical workflow. | Low to medium domain context. | Plain benefits, limitations, citations, safe error guidance. | Helpful and honest; no sales exaggeration. | Concise: benefit and limitation. Standard: workflow value. Deep: source-supported examples and caveats. | Benefit language can become promotional. | Errors and limitations must be understandable. | Emphasize workflow value, trust, limitations, expected benefit. | Unsupported benefit claims, hidden limitations. | Benefits must cite source facts; limitations cannot be dropped. | R280-AUDIENCE-CUSTOMER, R280-ERROR-SAFE-COPY |
| Beginner | Digital.gov plain language; NN/g scannability; Google PAIR expectation setting | Learn what the project does in dependency order without assumed jargon. | First exposure or onboarding. | Low assumed prior context. | Definitions, ordered explanation, citations after plain claims. | Plain and respectful; no infantilizing. | Concise: shortest plain explanation. Standard: dependency-order walkthrough. Deep: source-supported examples with defined terms. | Jargon may remain untranslated or unexplained. | Language-of-parts and glossary metadata help comprehension. | Explain plainly, avoid assumed jargon, order dependencies. | Jargon-only output, hidden source-backed caveats. | Simplification cannot remove cited facts or evidence. | R280-AUDIENCE-BEGINNER, R280-DEPTH-ORDER |
| Global viewer | W3C i18n/WAI; Digital.gov plain language; ONS task/knowledge variance | Understand the project across cultures, scripts, and language directions. | International review or non-local audience. | Variable. | Culturally neutral wording, language/script metadata, citations. | Neutral, internationally understandable, no local idioms. | Concise: neutral summary. Standard: neutral framing with context. Deep: source-supported examples that survive translation. | Idioms, direction, CJK/no-space, and RTL handling. | Correct language/direction metadata is required. | Use culturally neutral phrasing and preserve audience framing. | Local idioms, romanized fallback where native script required. | Translation must preserve selected audience/depth and evidence bindings. | R280-AUDIENCE-GLOBAL, R280-S6-DIRECTION |

## Golden Rules

- Audience controls emphasis; depth controls amount and structure.
- Audience-specific examples are allowed only when source-supported.
- Deep output cannot add uncited caveats, examples, tradeoffs, pros/cons, or
  implications.
- Concise output cannot hide required source-backed caveats.
- Standard output cannot be identical to concise.
- Translation must preserve audience framing in body text, not only metadata.
- UI and exports must show the audience/depth that generated the transcript.

## Rejected Persona Inputs

- Private personality inference.
- Runtime personality inference.
- Demographic stereotypes.
- Unsupported audience claims.
- Real personal data.
- Hidden reviewer strategy.
- Provider output or payload content.
- Private roadmap or provider strategy assumptions.
- Audience claims not supported by public product contract or cited project
  source evidence.
