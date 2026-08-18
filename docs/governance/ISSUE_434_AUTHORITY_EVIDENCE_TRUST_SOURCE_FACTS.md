# Issue 434 Authority-Evidence and Trust Source Facts

Status: frozen documentation source record  
Access date: 2026-08-17  
Activation: `NONE`  
Authority effect: `NO_AUTHORITY_EFFECT`

## Repository and route facts

- Repository: `imrohitagrawal/narratwin-ai`.
- Issue: `#434`, Child B of controller `#426`.
- Exact base and Child A squash merge:
  `87b8504ca8d5e094394343aeaa4ef5bad46133d5`.
- Exact base tree and Child A reviewed tree:
  `8a629b82d3ebf85174c7391745a12e17bbf3820f`.
- Child A reviewed tree-equivalent head:
  `9f82b641c3a35d8122d2e0640ecbdd769457b189`.
- Child A PR `#433` binary diff SHA-256:
  `c2293d4c87f1c9af451daca5cae70a65ef2093ef69fc5b0059877b4ec08d1cb1`.
- Child A completed with 18 paths and 4,107 charged lines after eligible
  non-author approval review `4949634246`, final OWNER comment `5313522538`,
  and successful merged-main run `32009462043`.
- Issue #434 body SHA-256:
  `6096803a39364cb45738c68e4899e24c6212b352d3b57a80d02934a8e79676f5`.
- Original OWNER approval comment `5313883532` SHA-256:
  `aaac7acfee0ea15265a4977602316eb65163e5fa56a77632f73385e4a0749e7f`.
- The original route owns 22 exact paths. Later bounded OWNER resets add only
  the reconstruction verifier and its focused test as paths 23 and 24; they do
  not widen the 5,600-line aggregate cap or activate authority.
- Latest bounded schema-context reset: Child comment `5328617265` and parent
  decision `5328616970`. Earlier reset evidence remains historical and is not
  rewritten.
- Approval expires at `2026-09-30T23:59:59Z`.

These are delivery and historical facts, not accepted authority evidence.
GitHub state must still be revalidated at review and merge time.

## Frozen technical sources

1. RFC 8032, “Edwards-Curve Digital Signature Algorithm (EdDSA),” including
   section 7.1 Ed25519 vectors:
   <https://www.rfc-editor.org/rfc/rfc8032>.
2. NIST SP 800-57 Part 1 Revision 5, “Recommendation for Key Management:
   Part 1 – General”:
   <https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final>.
3. `cryptography` 50.0.0 Ed25519 verification API:
   <https://cryptography.io/en/50.0.0/hazmat/primitives/asymmetric/ed25519/>.
4. `cryptography==50.0.0` release and license metadata:
   <https://pypi.org/project/cryptography/50.0.0/>.
5. The Update Framework specification 1.0.36, Git tag commit
   `59e601ed29c0d2e497264ae8b31c11b8ef07df1e`, used only as design guidance
   for independently rooted rotation, rollback/freeze resistance, and
   reconstruction:
   <https://theupdateframework.github.io/specification/v1.0.36/>.

The implementation uses the published RFC vector and only public-key
verification. It contains no private key, signing function, key generator,
TUF implementation, NIST certification claim, or general protocol proof.

## Accepted historical inputs

- Issue `#427` and its closeout comment `5296192826` define the nonactivating
  architecture kernel and strict `A -> B -> C -> D -> E -> F` order.
- Issue `#431` and closeout comment `5313543617`, plus parent reconciliation
  comment `5313546357`, establish the completed Child A predecessor.
- The accepted architecture proposal has SHA-256
  `794c2e90034a8012363a6a859dd3bac826280452e787b8a7afe5a49164849b29`.
- Child A's normative contract, three schemas, matrices, fixtures, ADR 0061,
  and verifier are structurally authoritative predecessor contracts. They are
  not accepted/current/active authority objects.

## Current Child B facts

Child B defines documentation-quality, offline verification contracts for
signed authority-evidence envelopes, independently supplied root pins and
expected history heads, producer-key lifecycle, explicit-time freshness,
root-compromise invalidation, reconstruction, replay, and distinct historical
and current verdicts. Typed precedence is
`CONFLICTING > INVALID > UNAVAILABLE > VALID`.

All fixtures use `.invalid` identities and are visibly non-authoritative.
No network, ambient clock, persistent store, credential, provider, spending,
media, deployment, publication, release, or production capability is created.

## Unresolved and future facts

- Issue `#432` is unmerged OWNER source authority only. It is outside Child B
  and does not alter current repository authority.
- Inserting `#432` after B and before C requires a separately audited parent
  `#426` amendment after Child B merge and merged-main verification.
- Child C retains projection, CAS, persistence, and bootstrap ownership; Child
  D retains audit/receipt coordination; Child E retains acquisition and
  historical reconciliation; Child F retains integrated kernel/oracle work.
- Eligible non-author approval, final exact-head OWNER approval, protected
  merge, merged-main checks, and issue closeout remain future GitHub events.
- Release remains No-Go. A green verifier or signature never creates authority.
