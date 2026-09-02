"""Fail-closed Stage 8 scope and budget routes for governed Cut 1 prerequisites."""
from __future__ import annotations

import hashlib
import json
import re
import stat
import subprocess
import unicodedata
from pathlib import Path
from typing import Any, Callable

from scripts.governance_preflight_v1 import validate_governance_preflight
from scripts.guardrails_check import cleanup_authority_anchor_failures

ISSUE150_BRANCH = "cut1-process-150-semgrep-mcp-renewal"
ISSUE460_BRANCH = "security-460-semgrep-override-removal"
ISSUE451_BRANCH = "docs/cut1-post-443-reconciliation-451"
ISSUE452_BRANCH = "docs/cut1-acceptance-provider-contract-452"
ISSUE459_BRANCH = "lane-a-cut1-459-controlled-presenter"
ISSUE459_T03_BRANCH = "stage8-459-t03-presenter-derivatives"
ISSUE459_T05A_BRANCH = "stage8-459-t05a-grounded-narration-handoff"
ISSUE459_T05B_BRANCH = "stage8-459-t05b-audio-caption-authority"
ISSUE468_BRANCH = "governance-468-scoped-merge-cleanup"
ISSUE466_BRANCH = "cut1-466-t05a-presenter-source-integrity"
ISSUE471_BRANCH = "governance-471-cleanup-authority-anchor"
ISSUE473_BRANCH = "governance-473-cleanup-anchor-consumer-fixture"
ISSUE475_BRANCH = "cut1-475-t05b-runtime-receipt-binding"
ISSUE478_BRANCH = "cut1-process-478-pr477-status-closeout"
ISSUE479_BRANCH = "cut1-process-479-t05c-listening-authority"
ISSUE482_BRANCH = "cut1-process-482-dependency-security-refresh"
ISSUE495_BRANCH = "stage8-495-browserslist-security-refresh"
ISSUE499_BRANCH = "stage8-499-pypdf-6-16-2-security-refresh"
ISSUE502_BRANCH = "stage8-502-frontend-musl-runtime-security"
ISSUE386_BRANCH = "cut1-process-386-modular-route-enforcement"
ISSUE413_BRANCH = "cut1-process-413-frontend-runtime-openssl"
ISSUE405_BRANCH = "process-405-heartbeat2-main-reliability"
ISSUE428_BRANCH = "cut1-process-428-nanoid-3-3-18-security"
ISSUE403_BRANCH = "cut1-process-403-nanoid-3-3-17-security"
ISSUE401_BRANCH = "cut1-process-401-pypdf-6-15-0-security"
ISSUE396_BRANCH = "cut1-process-396-js-yaml-4-3-1-security"
ISSUE385_BRANCH = "stage8-385-issue280-language-oracle"
ISSUE384_BRANCH = "stage8-384-presenter-asset-route"
ISSUE383_BRANCH = "stage8-383-presenter-assets"
ISSUE382_BRANCH = "stage8-382-cut1-narration-lock"
ISSUE367_BRANCH = "stage8-367-presenter-registry"
ISSUE397_BRANCH = "stage8-397-presenter-asset-adr-classifier"
ISSUE393_BRANCH = "stage8-393-historical-digest-test-isolation"
ISSUE368_BRANCH = "stage8-368-cut1-local-tts-audio"
ISSUE368_PROMPT_BRANCH = "stage8-368-cut1-google-tts-prompt-contract"
ISSUE368_ADAPTER_BRANCH = "stage8-368-cut1-google-tts-adapter-implementation"
ISSUE368_IMPLEMENTATION_BRANCH = "stage8-368-cut1-google-tts-runtime-transport"
ISSUE368_QUOTA_FIX_BRANCH = "stage8-368-google-tts-quota-project-binding-fix"
ISSUE368_BINDING_COMPAT_BRANCH = "stage8-issue-368-google-presenter-binding-compat"
ISSUE368_AUTH_TRANSPORT_BRANCH = "stage8-368-google-auth-public-transport-fix"
ISSUE368_TIMEOUT_BRANCH = "stage8-368-google-tts-long-response-timeout"
ISSUE494_BRANCH = "stage8-494-google-tts-failure-diagnostics"
ISSUE498_BRANCH = "stage8-498-google-tts-official-grpc"
ISSUE415_BRANCH = "stage8-415-pr-body-live-state-reconciliation"
ISSUE415_CORRECTION_BRANCH = "stage8-415-pr-body-consistency-canary-fix"
ISSUE486_BRANCH = "stage8-486-reviewer-impact-summary"
ISSUE486_PROTECTED_BRANCH = "stage8-486-reviewer-impact-protected-sources"
ISSUE486_HASH_CLEANUP_BRANCH = "stage8-486-reviewer-impact-hash-cleanup"
ISSUE421_BRANCH = "stage8-421-cut1-atomic-project-facts"
ISSUE424_BRANCH = "stage8-424-master-program-authority-prelog"
ISSUE386_BASE = "48fc32a2689c9bbc03742d774f3eadb8a500dafc"
ISSUE368_BASE = "ef9cabc23762560912d99f10831241b8a65b869c"
ISSUE368_PROMPT_BASE = "ba77d59b193da8064d67261e13fb50756c2bd9e8"
ISSUE368_IMPLEMENTATION_BASE = "6766da34d73e301358f84f8eefb0985927292a26"
ISSUE368_QUOTA_FIX_BASE = "9c165f739788fb0f09b315673f9125d700d6a96b"
ISSUE368_BINDING_COMPAT_BASE = "c41c35db811297fbeff0524dfe21ec49fa7c0de9"
ISSUE368_REFRESH_TRANSPORT_BASE = "92e7666df46e5dcc3eea80d17b87026d4aa4dc5c"
ISSUE368_TIMEOUT_BASE = "26258de9131c7a92b8a94ab949a57727b125dee5"
ISSUE494_BASE = "ca49843ada493162fa02ff7331b7c6adf3b505c9"
ISSUE494_FROZEN_HEAD = "c217a088af84f62138f874a164bdbb75cc0f5987"
ISSUE494_TRANSITION_BASE = "99f1d6a46bf9ee42d28aa04f46792ea56f392ab2"
ISSUE494_TRANSITION_MERGE = "97671772b7ab8ef2c583cecde98f35a9e472457b"
ISSUE494_TRANSITION_COMMENT = "5499248540"
ISSUE494_TRANSITION_SHA256 = "3c0968ef0827dfa314a8591230e410b4dd5a4b4092223b5f76fdc72499bbe9a3"
ISSUE498_BASE = "8fb9b6d143515a6e5cfe3c395477e51696fe782b"
ISSUE498_TREE = "21b5c26355262482b02554d4115fc5567b6fb253"
ISSUE498_FREEZE_COMMENT = "5500521261"
ISSUE498_FREEZE_SHA256 = "fafc0f0a8ae18c9cc08d9dbab668235546f652aa780256792d5d1cb0e8f9f58b"
ISSUE498_AMENDMENT_COMMENT = "5500539931"
ISSUE498_AMENDMENT_SHA256 = "30faa0f1062545413efaa7b6e9bc38f9b2cd82f2554078f666aac04e4f8ef843"
ISSUE498_BASE_AMENDMENT_COMMENT = "5504413401"
ISSUE498_BASE_AMENDMENT_SHA256 = "f575ac4c5eb75a2d7e45740e90b4652d08cd5601837a29a2dffe477279e604e9"
ISSUE498_TOPOLOGY_COMMENT = "5504600826"
ISSUE498_TOPOLOGY_SHA256 = "ec2477cfc8ce73eb624ce3e4b154b34336859fb100997dcfb6202234f191205f"
ISSUE498_REVIEW_CORRECTION_COMMENT = "5504653805"
ISSUE498_REVIEW_CORRECTION_SHA256 = (
    "a5cea09fcf3964caabd34ea7ea3a1ff991bc79599a2442b3680b960f5b8c7b5e"
)
ISSUE498_TRACEBACK_CORRECTION_COMMENT = "5504746823"
ISSUE498_TRACEBACK_CORRECTION_SHA256 = (
    "9a179acb4bdc513cb2a6d122ebe271885ee927baf4972e8113f8ca66f1137217"
)
ISSUE498_MERGE_PARITY_COMMENT = "5504929555"
ISSUE498_MERGE_PARITY_SHA256 = (
    "ec19733768f13672b8d322ae262c19fd8316c69a91ce197784f7cd5783b0b95c"
)
ISSUE498_COMMIT_TOPOLOGY: tuple[tuple[str | None, str], ...] = (
    ("5245393b2237cf8bcc25a652d885186b4d1c18f1", "test(tts): freeze official gRPC transport RED (#498)"),
    ("e8a0d9b7290d2f8af01994bdd9a1fd12851734cc", "feat(tts): add governed official unary gRPC transport (#498)"),
    ("6fcb1b28f3991f07d38924654fa812ede5381f06", "chore(tts): make channel-close failure observable (#498)"),
    ("3fd77f31f01ffbb4919e6ec0b8cdded300fade4a", "test(tts): bind grpc route to security-correct base (#498)"),
    ("d942c738c341b3357e4f1b41d28606f5ca755157", "fix(tts): advance grpc route after security prerequisite (#498)"),
    ("d59e8b6c9d389aa82566b541fb4fa57c7530bd97", "test(tts): require hosted SDK test dependency (#498)"),
    ("2adb5107d181b475a752174e4200c0d396ccdc88", "fix(tts): install official SDK for hosted tests (#498)"),
    ("91bdda7ae542118b9caa4b002eab3ae5bb25ec89", "test(tts): enforce exact grpc TDD topology (#498)"),
    ("149b98ddadfbd4adb8e5532c9b2c892a03eba5f1", "test(tts): freeze grpc boundary corrections (#498)"),
    ("94e9dab839fab39f8d526467bcc6a351f92e14e1", "fix(tts): close grpc security and truth gaps (#498)"),
    ("c6a973b09152d9fe4c59f08f13fb937e2e191600", "fix(tts): bind final grpc review corrections (#498)"),
    ("f452791a96e4ed394e37d44869080293dcf59567", "test(tts): freeze grpc traceback redaction (#498)"),
    ("23da78cc8807ab590bdc94a15ea94a6a31cd4c71", "fix(tts): discard grpc traceback inputs (#498)"),
    ("0f90f196f3992c487608476fe74767271b116ee6", "fix(tts): bind final grpc traceback correction (#498)"),
    ("233576f798b42cf09874e7d7ea896932886751c9", "test(stage8): freeze Issue498 merge topology parity (#498)"),
    (None, "fix(stage8): validate Issue498 direct and merge heads (#498)"),
)
ISSUE368_BINDING_COMPAT_AUTHORITY = (
    "5485581802", "c81d57d6adf081aaf6ec2bf8c94f4513ca7e363910a669efc3551d5b3b4eae3f",
    "5485633036", "8ccd797c3fac7802923a04aff0ac82d64363d8d9d25366a5365eef98b5436bd2",
    "5485657599", "8bde1e31e0b3e9642f39d2847b07d6818ed1e5ad14d05b2eb6c0af17b1f2e084",
    "5485702633", "3654edbbbc295cf2ce5a3206a4856c5987529458fe5742cbc3fd544a71024ddc",
    "5485891564", "6139a366e29d88affe418b9b912a7f31c10ca973f0ce0bf5ec3a8f93b2d131a5",
)
ISSUE421_BASE = "a868137fab607ae75d4b272301e9fc52b898e15c"
ISSUE424_BASE = "afcf0325c3ec925b68b770eda0bb8c839bcce4dd"
ISSUE486_BASE = "01857dc1ffa322700179d301925b444a04f166fa"
ISSUE486_PROTECTED_BASE = "f55f39bea1e009050c9d3f5e2f829cc8557f11d5"
ISSUE486_HASH_CLEANUP_BASE = "a2a9dfd044610b2bd51b37c0d914e09c1b3837b9"
ISSUE468_BASE = "35f7beddc9f5ad8c109011bce05eef077c8194f6"
ISSUE150_BASE = "a02286240212ad8958915aec01aa5ebaf60fa705"
ISSUE460_BASE = "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
ISSUE451_BASE = "59db96aaab6c4e75b12d134dc9b02330c5a982ac"
ISSUE452_BASE = "97e8173c2ec1323aa9ced23d43059bca2e5a204f"
ISSUE459_BASE, ISSUE459_FROZEN_HEAD = "ab97b6eecba6db9c66c37d19b29257c7398f3ab7", "570239effbcae3990a24ffdc809622f02364ff0d"
ISSUE459_TRANSITION_BASE, ISSUE459_TRANSITION_MERGE = "285458f22a5d8786c359c6e4ebf0f9acd82ead96", "b569e0bbc6175423706558aa1cc78486a09dfbe5"
ISSUE459_T03_BASE = "4ef3a8ba70cbf97b7704f5f589b0887f840081cb"
ISSUE459_T03_AUTHORITY_COMMENT = "5463568867"
ISSUE459_T03_AUTHORITY_SHA256 = "728705c278db4b05d4072bcacc3af657b069662e21fbf4f5f5ee2f934a155da8"
ISSUE459_T03_CORRECTION_COMMENT = "5463979365"
ISSUE459_T03_CORRECTION_SHA256 = "c8816f6243e5810267b66c84fcaa6bd471d78fca24463f6b9e46352a93c42113"
ISSUE459_T03_DEPENDENCY_COMMENT = "5464081073"
ISSUE459_T03_DEPENDENCY_SHA256 = "1e07f4d261216e3d3b218160e1b46bf84f3f395fbe816db926f004314182f369"
ISSUE459_T03_MYRA_CORRECTION_COMMENT = "5464690216"
ISSUE459_T03_MYRA_CORRECTION_SHA256 = "4b69e4707492c6e6c7d8b8527680d8ef0987043745220e19e0c2036faaf62bfa"
ISSUE459_T05A_BASE = "0d70fa8e27ad4760249d75e7782ac06b5d68b173"
ISSUE459_T05A_AUTHORITY_COMMENT = "5465050919"
ISSUE459_T05A_AUTHORITY_SHA256 = "ab0d0b486bf77eac59db2b83c0d33bd0ae61bb52ed26b37b4d7a8402b2ec31c8"
ISSUE459_T05B_BASE = "bfb8487760dc6aeef8b05af95e0ecd40d0076f3a"
ISSUE471_BASE = "7eb4b99d7bc2bcf11cfc8c959baacb6cf3a21e81"
ISSUE473_BASE = "55a0810e2ff327490d6dbadbf58580c06edef600"
ISSUE475_BASE = "fb963f92057b8ccd5c0c070a3c9b5406ee9e884f"
ISSUE478_BASE = "81c1884157502e8a911df63c1d9d0a1704964d63"
ISSUE478_ROUTE_COMMENT = "5473694821"
ISSUE478_ROUTE_SHA256 = "0b46e4d6bbf091906e82ca8a7d26c9f7b2195a2866d6e436932f9a1100f93fc7"
ISSUE478_BRANCH_COMMENT = "5473718767"
ISSUE478_BRANCH_SHA256 = "3c42143d50b21916cc9e063f9a06855b7d57b398310b19dfd64cb9309613e8f2"
ISSUE478_REVIEW_COMMENT = "5474383480"
ISSUE478_REVIEW_SHA256 = "444a43fcd953c961d31d3cdc3387e12a8c2fc3d297c1e6805eba21ba3e893b1f"
ISSUE479_BASE = "98fa8b41ccea68c840b5462bd5377057f4a3eb14"
ISSUE479_ROUTE_COMMENT = "5481284482"
ISSUE479_ROUTE_SHA256 = "bc878f9886a1decc2fbab102d1d9be7e8e23ab870a9850d486445564813dc2b4"
ISSUE479_CLARIFICATION_COMMENT = "5473637391"
ISSUE479_CLARIFICATION_SHA256 = "9a08ee1c2ce085cec47ca3981ccfa8a9e79c700b75fc8ab1f66b301417e1a05f"
ISSUE479_BUDGET_COMMENT = "5481522433"
ISSUE479_BUDGET_SHA256 = "6e71a7301a9e9f2eb7fb251a4d38b37f0101804f8cdfddd68f36f87d9961223e"
ISSUE479_FROZEN_HEAD = "773ba43e870a1a18785829c3093d8a74f4416078"
ISSUE479_TRANSITION_BASE = "9b5472a53844495a9d54637167ce48a33a572e11"
ISSUE479_TRANSITION_MERGE = "56f92e969c8de3d39bd452e6917cb8017a6abf98"
ISSUE479_TRANSITION_COMMENT = "5484097802"
ISSUE479_TRANSITION_SHA256 = "3f1dac2e24bb52caea5db6cf8ea1a224a7f776277af490cee4189595c316bf57"
ISSUE482_BASE = "98fa8b41ccea68c840b5462bd5377057f4a3eb14"
ISSUE495_BASE = "ca49843ada493162fa02ff7331b7c6adf3b505c9"
ISSUE499_BASE = "d1f5400f5c6dfec5d4b63eb3a83aa82e3330743f"
ISSUE499_TREE = "905f562c17e66abf1839e673940f80aca4330cfc"
ISSUE499_ROUTE_COMMENT = "5500895575"
ISSUE499_ROUTE_SHA256 = "e0a4fcfadb274efa6ca36e7b076d096e4e8a228de9b9321f6eaa740255c27ae2"
ISSUE502_BASE = "e1fe126372d5c5a06dc7d2f9c76cb205da8643e7"
ISSUE502_TREE = "76495e566a78a7951c33314ac742606c85ee92e5"
ISSUE502_ROUTE_COMMENT = "5507883668"
ISSUE502_ROUTE_SHA256 = "c114a3f11ac2a52f0834ac9f67119605c1f9d1623f6511eb42fd4c1426e6476f"
ISSUE495_TREE = "13f79eb5db44249f635a619e1b283279f25ba9f0"
ISSUE495_ROUTE_COMMENT = "5498387945"
ISSUE495_CORRECTION_COMMENT = "5498411811"
ISSUE495_HOSTED_CORRECTION_COMMENT = "5498589302"
ISSUE495_GUARDRAIL_CORRECTION_COMMENT = "5498765949"
ISSUE495_LOCK_SHA256 = "45b5f03df2b60ec9f10ade076507156a3c62d6fa7a7d2ca866a67396292d7c11"
ISSUE482_BODY_SHA256 = "736252b09e0b79a57e5ed8643f5b915feff7522693427fe2d48d4dba372c5289"
ISSUE482_ROUTE_COMMENT = "5481998106"
ISSUE482_ROUTE_SHA256 = "a006437d5b773fa2a6a555c0744b40b292d55224c4d60aa739fe9da5ab2af46f"
ISSUE482_CORRECTION_COMMENT = "5482139606"
ISSUE482_CORRECTION_SHA256 = "85ad9dbf5dcc91948f625a15c1b58c9306be2fc014c6e298e7ddb760a538e699"
ISSUE475_RUNTIME_COMMENT = "5470636741"
ISSUE475_RUNTIME_SHA256 = "27b21d3db0ec01f310ac5db57260ea656b3f73bac50a40b78106a99d823159fe"
ISSUE475_RECEIPT_COMMENT = "5470701562"
ISSUE475_RECEIPT_SHA256 = "415139a73d27173eb406654ca66acd0ecf928f40b4eea0d3d71a7572558a49c1"
ISSUE475_FREEZE_COMMENT = "5471056591"
ISSUE475_FREEZE_SHA256 = "239c2dcd903e0e5a056a2af4d9abdb80b8b148430c107549984f0ac2bb627348"
ISSUE475_HOSTED_COMMENT = "5471282345"
ISSUE475_HOSTED_SHA256 = "0cac623417e1645403dca44b4cdc9fe09e4f23efd6c0acdb5b28af1f6dd9ffe1"
ISSUE471_AUTHORITY_SHA256 = (
    "7222909116385fe74cbc7df6bbccb759687d2e4a6bf0e0637465679434de33ab",
    "30ba0f8e7b736293c4b6c110cbe9ce46bf7639507b0441bd37cb222bb62ae94f",
)
ISSUE459_T05B_AUTHORITY_COMMENT = "5466871459"
ISSUE459_T05B_AUTHORITY_SHA256 = "f53e919836ea5edd58620d789497d945f317c354d0b5405a88d49e570c778b28"
ISSUE459_T05B_CORRECTION_COMMENT = "5466962967"
ISSUE459_T05B_CORRECTION_SHA256 = "4d4cd204972abfa70b687f416813937b41329c930cf1676706ce278798579032"
ISSUE459_T05B_FINGERPRINT_CORRECTION_COMMENT = "5467038670"
ISSUE459_T05B_FINGERPRINT_CORRECTION_SHA256 = "41e41763e52382b3eeeea6f265dd42e2078293a3325e5df6c62f9e01d5bbc340"
ISSUE459_T05B_REVIEW_CORRECTION_COMMENT = "5467125295"
ISSUE459_T05B_REVIEW_CORRECTION_SHA256 = "6f05484d33e69ede373841fbb57755ae3139e5c1e06280252b8bc1558d42b263"
ISSUE459_T05B_HOSTED_PROVENANCE_COMMENT = "5467552503"
ISSUE459_T05B_HOSTED_PROVENANCE_SHA256 = "a00a8a8348303a82d46d3dcddddeeb0307d6af230118879a04fbda7ff4476ccb"
ISSUE466_BASE = "7eb4b99d7bc2bcf11cfc8c959baacb6cf3a21e81"
ISSUE466_FROZEN_HEAD = "24c778b4b7ac99b8bdcd34b094f51d5513723958"
ISSUE466_TRANSITION_BASE = "3b186af6f5787a47bbfa5f7aebaa2dc9661866ca"
ISSUE466_TRANSITION_MERGE = "23a12d6845f9e441d37f322da3cd73251b6de191"
ISSUE466_AUTHORITY_REVISION = "issue:466@2026-08-30T09:44:54Z"
ISSUE466_AUTHORITY_SHA256 = "3e4c9c483bdea609be70c46863a36f64a1900cac058615a22e213ea218c9212c"
ISSUE466_SPAN_SHA256 = "6ed0e9270ca03d6940ecc11e3e174d8024a54aba306f18d5b8eedb1ed9241396"
ISSUE466_FREEZE_COMMENT = "5467958861"
ISSUE466_FREEZE_SHA256 = "12699c91eaa0cb23dbd20622ef5aaf87238d9fca0cadba0d98d60cc349867fbf"
ISSUE466_CORRECTION_COMMENT = "5468026907"
ISSUE466_CORRECTION_SHA256 = "91682bed3814d7d89c70c635b690e5b6f47111d51fd5e800e82399e03fbc6398"
ISSUE466_SKILL_LEDGER_COMMENT = "5468042606"
ISSUE466_SKILL_LEDGER_SHA256 = "5a976b8a72f7df10f8bbfee746a7eb098293aae19e32e6abcab1c7e9a22ce0c1"
SECURITY_PREFLIGHTS = {
    150: ("Issue150SecurityRenewalPreflightV1", "e6a569cb6254ef58c36fb44e9cdece26e0816b49c9f62ce08e9d90f3843c97e3"),
    428: ("Issue428NanoidSecurityPreflightV1", "0d8da352c98855bc481581f1ca13cc2d4e994838b1afb31d974ad2b17caf7a9b"),
    460: ("GovernancePreflightV1", "62e230c6510c7ce88fef607e89254e3f3035fe8f49134abd200ba6124ac2d94b"),
}
ISSUE460_CORRECTION_PATHS = {
    "scripts/quality/check_issue16_spec_kit.py",
    "tests/unit/test_issue16_spec_kit_gate.py",
    "tests/unit/test_issue427_architecture_reset.py",
    "tests/unit/test_stage8_quality_gate.py",
}
ISSUE460_HOSTED_SECURITY_PATHS = {
    ".gitleaksignore",
    "scripts/ci/check_gitleaks_regression.py",
    "scripts/ci/dependency-security.sh",
    "tests/unit/test_gitleaks_regression.py",
}
ISSUE459_HOSTED_CORRECTION_PATHS = {".gitleaksignore", "scripts/ci/check_gitleaks_regression.py", "tests/unit/test_gitleaks_regression.py", "scripts/quality/check_stage8_docs.py", "tests/unit/test_stage8_quality_gate.py"}

ROUTES = {
    ISSUE502_BRANCH: {
        "docs/governance/preflights/issue-502.json",
        "frontend/Dockerfile",
        ".github/workflows/security.yml",
        "scripts/ci/docker-image-scan.sh",
        "scripts/ci/check_container_scan_consensus.py",
        "scripts/quality/stage8_node_security.py",
        "scripts/quality/check_stage8_docs.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_frontend_container_runtime.py",
        "tests/unit/test_stage8_node_security.py",
        "tests/unit/test_container_scan_consensus.py",
        "tests/unit/test_stage8_quality_gate.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0077-frontend-musl-scratch-runtime.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE479_BRANCH: {
        "docs/governance/preflights/issue-479.json", "backend/app/cut1_listening.py",
        "tests/unit/test_cut1_listening.py", "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py", "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0073-cut1-exact-hash-listening-authority.md", "docs/API_CONTRACT.md",
        "docs/DATA_MODEL.md", "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md", "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
    },
    ISSUE482_BRANCH: {
        "docs/governance/preflights/issue-482.json", "uv.lock",
        "tests/unit/test_dependency_security_contract.py",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py", "docs/THIRD_PARTY_NOTICES.md",
        "docs/QUALITY_GATES.md", "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE495_BRANCH: {
        "frontend/package-lock.json",
        "docs/governance/preflights/issue-495-browserslist-security-refresh.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_frontend_dependency_security_contract.py",
        "docs/ADR/0074-browserslist-4-28-8-security-refresh.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE499_BRANCH: {
        "docs/governance/preflights/issue-499-pypdf-6-16-2-security-refresh.json",
        "pyproject.toml",
        "uv.lock",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "docs/ADR/0075-pypdf-6-16-2-security-refresh.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE478_BRANCH: {
        "docs/STATUS.md",
        "docs/governance/preflights/issue-478.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
    },
    ISSUE475_BRANCH: {
        "backend/app/cut1_audio.py",
        "tests/unit/test_cut1_audio.py",
        "docs/governance/preflights/issue-475.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0071-cut1-audio-caption-authority.md",
        "docs/API_CONTRACT.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/QUALITY_GATES.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE468_BRANCH: {
        "AGENTS.md",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        "docs/governance/preflights/issue-468-scoped-merge-cleanup.json",
        "docs/STATUS.md",
        "docs/agent-context/context-policy-manifest-v1.json",
        "scripts/quality/check_stage8_docs.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE466_BRANCH: {
        "docs/governance/preflights/issue-466.json",
        "docs/governance/cut1-project-facts-v1.json",
        "backend/app/cut1_grounding.py",
        "tests/unit/test_cut1_atomic_grounding.py",
        "tests/unit/test_cut1_narration.py",
        "docs/ADR/0072-cut1-presenter-source-integrity.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE471_BRANCH: {
        "docs/governance/preflights/issue-471-cleanup-authority-anchor.json",
        "docs/STATUS.md",
        "scripts/guardrails_check.py", "tests/unit/test_guardrails_check.py",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE473_BRANCH: {
        "tests/unit/test_guardrails_check.py",
        "docs/governance/preflights/issue-473-cleanup-anchor-consumer.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/STATUS.md",
    },
    ISSUE459_T05B_BRANCH: {
        ".gitleaksignore",
        "docs/governance/preflights/issue-459-t05b.json",
        "backend/app/cut1_audio.py", "backend/app/tts_provider.py",
        "backend/app/stage6.py", "tests/unit/test_cut1_audio.py",
        "tests/unit/test_stage6_tts_provider.py",
        "docs/ADR/0071-cut1-audio-caption-authority.md",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md", "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md",
        "docs/TRACEABILITY.md", "docs/DATA_MODEL.md", "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "scripts/ci/check_gitleaks_regression.py",
        "tests/unit/test_gitleaks_regression.py",
    },
    ISSUE459_T05A_BRANCH: {
        "docs/governance/preflights/issue-459-t05a.json",
        "backend/app/cut1_grounding.py", "backend/app/narration.py",
        "tests/unit/test_cut1_atomic_grounding.py", "tests/unit/test_cut1_narration.py",
        "docs/ADR/0070-cut1-t05-grounded-narration-handoff.md",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md", "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE459_T03_BRANCH: {
        "pyproject.toml", "uv.lock",
        "docs/governance/preflights/issue-459-t03.json", "docs/governance/cut1-presenter-derivatives-v1.json",
        "frontend/public/demo/cut1/raj-waist-up.webp", "frontend/public/demo/cut1/myra-waist-up.webp",
        "backend/app/presenter_registry.py", "tests/unit/test_cut1_presenter_derivatives.py",
        "tests/unit/test_dependency_security_contract.py",
        "docs/ADR/0069-cut1-presenter-derivative-readiness-binding.md", "docs/THIRD_PARTY_NOTICES.md",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md", "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
    },
    ISSUE459_BRANCH: {
        "docs/governance/preflights/issue-459.json", "docs/governance/ISSUE_459_CONTROLLED_PRESENTER_PREFLIGHT_V1.md", "docs/governance/schemas/cut1-controlled-presenter-evidence-v1.schema.json", "docs/governance/cut1-controlled-presenter-red-corpus-v1.json",
        "scripts/quality/cut1_controlled_presenter.py", "tests/unit/test_cut1_controlled_presenter_red.py", "scripts/quality/check_quality_stage.py", "tests/unit/test_issue459_quality_dispatcher.py", "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
        "docs/reviews/ISSUE_459_ENTRY_GATE_REVIEW.md", "docs/QUALITY_GATES.md", "docs/STAGE_ISSUE_PLAN.md", "docs/PHASE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md", "backend/app/cut1_controlled_presenter.py", "tests/unit/test_cut1_controlled_presenter.py", "docs/ADR/0068-cut1-controlled-presenter-controller.md", *ISSUE459_HOSTED_CORRECTION_PATHS,
    },
    ISSUE460_BRANCH: {
        "docs/governance/preflights/issue-460.json", "docs/ADR/0069-semgrep-1-175-override-removal.md",
        "docs/RELEASE_CHECKLIST.md", "docs/RISK_REGISTER.md", "docs/SECURITY_AND_PRIVACY.md",
        "scripts/ci/check_semgrep_security.py", "tools/semgrep/pyproject.toml",
        "tools/semgrep/reviewed-inputs.sha256", "tools/semgrep/uv.lock",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py", "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/THIRD_PARTY_NOTICES.md", "docs/TRACEABILITY.md",
    } | ISSUE460_CORRECTION_PATHS | ISSUE460_HOSTED_SECURITY_PATHS,
    ISSUE452_BRANCH: {
        "docs/governance/preflights/issue-452.json",
        "docs/governance/schemas/cut1-human-realism-evaluation-v1.schema.json",
        "docs/governance/schemas/cut1-presenter-provider-acceptance-v1.schema.json",
        "docs/governance/cut1-blinded-human-evaluation-protocol-v1.json",
        "docs/governance/cut1-all-presenter-acceptance-matrix-v1.json",
        "docs/governance/cut1-provider-bakeoff-contract-v1.json",
        "docs/governance/cut1-presenter-contract-red-freeze-v1.json",
        "scripts/quality/cut1_presenter_contract.py",
        "tests/unit/test_cut1_presenter_contract.py",
        "scripts/quality/check_quality_stage.py",
        "tests/unit/test_issue452_quality_dispatcher.py",
        "tests/unit/test_quality_dispatcher.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0065-cut1-all-presenter-acceptance-provider-bakeoff.md",
        "docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md",
        "docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md",
        "docs/ENTERPRISE_READINESS_REGISTER.md",
        "docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md",
        "docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md",
        "docs/QUALITY_GATES.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE451_BRANCH: {
        "docs/PHASE_PLAN.md",
        "docs/STATUS.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_adversarial_convergence.py",
        "tests/unit/test_guardrails_check.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
    },
    ISSUE150_BRANCH: {
        "docs/governance/preflights/issue-150.json",
        "docs/ADR/0061-semgrep-1-172-mcp-override-renewal.md",
        "docs/RELEASE_CHECKLIST.md",
        "docs/RISK_REGISTER.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "scripts/ci/check_semgrep_security.py",
        "tools/semgrep/pyproject.toml",
        "tools/semgrep/reviewed-inputs.sha256",
        "tools/semgrep/uv.lock",
        "docs/governance/preflights/issue-428.json",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_frontend_dependency_security_contract.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0062-nanoid-3-3-18-security-refresh.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE424_BRANCH: {
        "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md",
        "docs/governance/narratwin-master-program-v1.json",
        "docs/governance/preflights/issue-424.json",
        "docs/reviews/ISSUE_424_EXECUTION_SPEC_REVIEW.md",
        "docs/reviews/ISSUE_424_CUT1_FALSE_SUCCESS_REVIEW.md",
        "docs/reviews/ISSUE_424_PLATFORM_SECURITY_LEARNING_REVIEW.md",
        "docs/ADR/0059-master-program-authority-and-route-bootstrap.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
    },
    ISSUE421_BRANCH: {
        "docs/governance/preflights/issue-421.json",
        "docs/governance/cut1-project-facts-v1.json",
        "backend/app/narration.py",
        "backend/app/cut1_grounding.py",
        "backend/app/rag/models.py",
        "backend/app/stage4.py",
        "backend/app/evaluation_lineage.py",
        "tests/unit/test_cut1_atomic_grounding.py",
        "tests/unit/test_cut1_narration.py",
        "tests/unit/test_evaluation_lineage.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0058-cut1-atomic-project-facts-grounding.md",
        "docs/API_CONTRACT.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE415_BRANCH: {
        ".github/pull_request_template.md", ".github/workflows/pr-body-consistency.yml", "AGENTS.md", "Makefile",
        "docs/ADR/0040-pr-body-live-state-reconciliation.md", "docs/CODEX_OPERATING_MODEL.md", "docs/QUALITY_GATES.md", "docs/STATUS.md",
        "docs/agent-context/context-policy-manifest-v1.json", "docs/governance/preflights/issue-415.json",
        "scripts/quality/pr_body_consistency.py", "scripts/quality/pr_body_consistency_cli.py", "scripts/quality/stage8_cut1_routes.py",
        "tests/fixtures/pr_body_consistency/live_pr.json", "tests/unit/test_pr_body_consistency.py", "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE415_CORRECTION_BRANCH: {
        ".github/workflows/pr-body-consistency.yml",
        "docs/STATUS.md",
        "docs/governance/preflights/issue-415.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_pr_body_consistency.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE486_BRANCH: {
        "docs/governance/preflights/issue-486-reviewer-impact-summary.json",
        ".github/pull_request_template.md",
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/REPOSITORY_GUARDRAILS.md",
        "docs/QUALITY_GATES.md",
        "docs/agent-context/context-policy-manifest-v1.json",
        "docs/STATUS.md",
    },
    ISSUE486_PROTECTED_BRANCH: {
        "AGENTS.md",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        "docs/agent-context/context-policy-manifest-v1.json",
        "docs/governance/preflights/issue-486-protected-reviewer-impact.json",
        "docs/STATUS.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE486_HASH_CLEANUP_BRANCH: {
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
        "docs/governance/preflights/issue-486-protected-hash-cleanup.json",
        "docs/STATUS.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE413_BRANCH: {
        "docs/governance/preflights/issue-413.json",
        "frontend/Dockerfile",
        "scripts/ci/docker-image-scan.sh",
        "scripts/ci/check_container_scan_consensus.py",
        "tests/unit/test_container_scan_consensus.py",
        "tests/unit/test_frontend_container_runtime.py",
        "tests/unit/test_stage8_quality_gate.py",
        "scripts/quality/stage8_cut1_routes.py",
        "scripts/quality/stage8_node_security.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_node_security.py",
        "docs/ADR/0057-frontend-runtime-openssl-3-6-4.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/QUALITY_GATES.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/STAGE_ISSUE_PLAN.md",
    },
    ISSUE368_ADAPTER_BRANCH: {
        "docs/governance/preflights/issue-368.json",
        "backend/app/narration.py",
        "backend/app/tts_provider.py",
        "backend/app/stage6.py",
        "tests/unit/test_cut1_narration.py",
        "tests/unit/test_stage6_tts_provider.py",
        "tests/unit/test_stage6_multilingual.py",
        "tests/api/test_stage6_multilingual_api.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/ARCHITECTURE.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/API_CONTRACT.md",
        "docs/DATA_MODEL.md",
    },
    ISSUE368_IMPLEMENTATION_BRANCH: {
        "docs/governance/preflights/issue-368.json",
        "backend/app/google_tts_runtime.py",
        "backend/app/tts_provider.py",
        "pyproject.toml",
        "uv.lock",
        "tests/unit/test_google_tts_runtime.py",
        "tests/unit/test_dependency_security_contract.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/ARCHITECTURE.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE368_QUOTA_FIX_BRANCH: {
        "backend/app/google_tts_runtime.py",
        "backend/app/tts_provider.py",
        "tests/unit/test_google_tts_runtime.py",
        "tests/unit/test_stage6_tts_provider.py",
        "docs/governance/preflights/issue-368.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/API_CONTRACT.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/ci/verify_branch_protection.py",
        "tests/unit/test_branch_protection_verifier.py",
        "tests/unit/test_governance_preflight_github.py",
        "docs/REPOSITORY_GUARDRAILS.md",
        "docs/agent-context/context-policy-manifest-v1.json",
    },
    ISSUE368_BINDING_COMPAT_BRANCH: {
        "backend/app/tts_provider.py",
        "tests/unit/test_stage6_tts_provider.py",
        "docs/governance/preflights/issue-368-provider-binding-compat.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/STATUS.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE368_AUTH_TRANSPORT_BRANCH: {
        "backend/app/google_tts_runtime.py",
        "tests/unit/test_google_tts_runtime.py",
        "docs/governance/preflights/issue-368-auth-transport.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/STATUS.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE368_TIMEOUT_BRANCH: {
        "backend/app/google_tts_runtime.py",
        "backend/app/tts_provider.py",
        "tests/unit/test_google_tts_runtime.py",
        "tests/unit/test_stage6_tts_provider.py",
        "docs/governance/preflights/issue-368-google-tts-timeout.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/STATUS.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE494_BRANCH: {
        "backend/app/tts_provider.py",
        "tests/unit/test_stage6_tts_provider.py",
        "docs/governance/preflights/issue-494-google-tts-failure-diagnostics.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/STATUS.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE498_BRANCH: {
        "backend/app/google_tts_runtime.py",
        "backend/app/tts_provider.py",
        "tests/unit/test_google_tts_runtime.py",
        "tests/unit/test_stage6_tts_provider.py",
        "tests/unit/test_dependency_security_contract.py",
        "pyproject.toml",
        "uv.lock",
        "docs/governance/preflights/issue-498-google-tts-official-grpc.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE368_PROMPT_BRANCH: {
        "docs/governance/preflights/issue-368.json",
        "docs/governance/cut1-google-gemini-tts-style-prompts-v1.json",
        "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE368_BRANCH: {
        "docs/governance/preflights/issue-368.json",
        "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/ADR/0002-provider-agnostic-adapters.md",
        "docs/ARCHITECTURE.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE382_BRANCH: {
        "docs/governance/preflights/issue-382.json",
        "backend/app/narration.py",
        "tests/unit/test_cut1_narration.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0055-cut1-narration-speech-lock.md",
        "docs/ARCHITECTURE.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE405_BRANCH: {
        "docs/governance/preflights/issue-405.json",
        ".github/workflows/ci.yml",
        "scripts/ci/heartbeat2-browser.sh",
        "scripts/ci/heartbeat2_evidence.py",
        "tests/unit/test_heartbeat2_evidence.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md",
        "docs/STATUS.md",
    },
    ISSUE428_BRANCH: {
        "docs/governance/preflights/issue-428.json", "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_frontend_dependency_security_contract.py", "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0062-nanoid-3-3-18-security-refresh.md", "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    ISSUE403_BRANCH: {
        "docs/governance/preflights/issue-403.json",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_frontend_dependency_security_contract.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "scripts/ci/check_container_scan_consensus.py",
        "tests/unit/test_container_scan_consensus.py",
        "docs/ADR/0053-nanoid-3-3-17-security-refresh.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    ISSUE401_BRANCH: {
        "docs/governance/preflights/issue-401.json",
        "pyproject.toml",
        "uv.lock",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0052-pypdf-6-15-0-security-refresh.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    ISSUE396_BRANCH: {
        "docs/ADR/0051-js-yaml-4-3-1-security-refresh.md",
        "docs/governance/preflights/issue-396.json",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    ISSUE386_BRANCH: {
        "docs/governance/preflights/issue-386.json",
        "scripts/quality/stage8_cut1_routes.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "tests/acceptance/test_issue280_local_e2e_demo.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    },
    ISSUE385_BRANCH: {
        "docs/governance/preflights/issue-385.json",
        "tests/acceptance/test_issue280_local_e2e_demo.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    },
    ISSUE384_BRANCH: {
        "docs/governance/preflights/issue-384.json",
        "scripts/quality/check_stage8_docs.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE383_BRANCH: {
        "docs/governance/preflights/issue-383.json",
        "frontend/public/demo/myra-synthetic-presenter.webp",
        "frontend/public/demo/raj-synthetic-presenter.webp",
        "tests/unit/test_cut1_presenter_assets.py",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE367_BRANCH: {
        "docs/governance/preflights/issue-367.json",
        "backend/app/presenter_registry.py",
        "backend/app/presenter_registry.json",
        "tests/unit/test_cut1_presenter_registry.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0054-cut1-presenter-registry.md",
        "docs/ARCHITECTURE.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE397_BRANCH: {
        "docs/governance/preflights/issue-397.json",
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/REPOSITORY_GUARDRAILS.md",
        "docs/agent-context/context-policy-manifest-v1.json",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE393_BRANCH: {
        "docs/governance/preflights/issue-393.json",
        "docs/governance/preflights/issue-396.json",
        "docs/ADR/0051-js-yaml-4-3-1-security-refresh.md",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "tests/unit/test_dependency_security_contract.py",
        "scripts/ci/check_container_scan_consensus.py",
        "tests/unit/test_container_scan_consensus.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
}
ROUTE_ISSUES = {ISSUE452_BRANCH: 452, ISSUE451_BRANCH: 451, ISSUE150_BRANCH: 150, ISSUE424_BRANCH: 424, ISSUE421_BRANCH: 421, ISSUE415_BRANCH: 415, ISSUE415_CORRECTION_BRANCH: 415, ISSUE413_BRANCH: 413, ISSUE368_ADAPTER_BRANCH: 368, ISSUE368_IMPLEMENTATION_BRANCH: 368, ISSUE368_QUOTA_FIX_BRANCH: 368, ISSUE368_PROMPT_BRANCH: 368, ISSUE368_BRANCH: 368, ISSUE405_BRANCH: 405, ISSUE428_BRANCH: 428, ISSUE403_BRANCH: 403, ISSUE401_BRANCH: 401, ISSUE396_BRANCH: 396,
                ISSUE386_BRANCH: 386, ISSUE385_BRANCH: 385,
                ISSUE384_BRANCH: 384, ISSUE383_BRANCH: 383, ISSUE397_BRANCH: 397,
                ISSUE393_BRANCH: 393, ISSUE382_BRANCH: 382, ISSUE367_BRANCH: 367}
ROUTE_ISSUES[ISSUE468_BRANCH] = 468
ROUTE_ISSUES[ISSUE486_BRANCH] = 486
ROUTE_ISSUES[ISSUE486_PROTECTED_BRANCH] = 486
ROUTE_ISSUES[ISSUE486_HASH_CLEANUP_BRANCH] = 486
TOTAL_LIMITS = {ISSUE452_BRANCH: 3600, ISSUE451_BRANCH: 600, ISSUE150_BRANCH: 1000, ISSUE424_BRANCH: 8500, ISSUE421_BRANCH: 4000, ISSUE415_BRANCH: 5000, ISSUE415_CORRECTION_BRANCH: 800, ISSUE413_BRANCH: 5000, ISSUE368_ADAPTER_BRANCH: 5600, ISSUE368_IMPLEMENTATION_BRANCH: 3600, ISSUE368_QUOTA_FIX_BRANCH: 2800, ISSUE368_PROMPT_BRANCH: 1000, ISSUE368_BRANCH: 3200, ISSUE405_BRANCH: 800, ISSUE428_BRANCH: 500, ISSUE403_BRANCH: 650, ISSUE401_BRANCH: 600, ISSUE396_BRANCH: 500,
                ISSUE386_BRANCH: 700, ISSUE385_BRANCH: 350,
                ISSUE384_BRANCH: 500, ISSUE383_BRANCH: 700, ISSUE397_BRANCH: 500,
                ISSUE393_BRANCH: 700, ISSUE382_BRANCH: 3200, ISSUE367_BRANCH: 2000}
TOTAL_LIMITS[ISSUE468_BRANCH] = 1500
TOTAL_LIMITS[ISSUE486_BRANCH] = 1400
TOTAL_LIMITS[ISSUE486_PROTECTED_BRANCH] = 700
TOTAL_LIMITS[ISSUE486_HASH_CLEANUP_BRANCH] = 700
ROUTE_ISSUES[ISSUE471_BRANCH] = 471
TOTAL_LIMITS[ISSUE471_BRANCH] = 1400
ROUTE_ISSUES[ISSUE473_BRANCH] = 473
TOTAL_LIMITS[ISSUE473_BRANCH] = 580
ROUTE_ISSUES[ISSUE475_BRANCH] = 475
TOTAL_LIMITS[ISSUE475_BRANCH] = 1800
ROUTE_ISSUES[ISSUE478_BRANCH] = 478
TOTAL_LIMITS[ISSUE478_BRANCH] = 800
ROUTE_ISSUES[ISSUE479_BRANCH] = 479
TOTAL_LIMITS[ISSUE479_BRANCH] = 2600
ROUTE_ISSUES[ISSUE482_BRANCH] = 482
TOTAL_LIMITS[ISSUE482_BRANCH] = 3200
ROUTE_ISSUES[ISSUE495_BRANCH] = 495
TOTAL_LIMITS[ISSUE495_BRANCH] = 1300
ROUTE_ISSUES[ISSUE499_BRANCH] = 499
TOTAL_LIMITS[ISSUE499_BRANCH] = 1000
ROUTE_ISSUES[ISSUE502_BRANCH] = 502
TOTAL_LIMITS[ISSUE502_BRANCH] = 4660
ROUTE_ISSUES[ISSUE459_BRANCH] = 459
TOTAL_LIMITS[ISSUE459_BRANCH] = 4300
ROUTE_ISSUES[ISSUE459_T03_BRANCH] = 459
TOTAL_LIMITS[ISSUE459_T03_BRANCH] = 2400
ROUTE_ISSUES[ISSUE459_T05A_BRANCH] = 459
TOTAL_LIMITS[ISSUE459_T05A_BRANCH] = 2200
ROUTE_ISSUES[ISSUE459_T05B_BRANCH] = 459
TOTAL_LIMITS[ISSUE459_T05B_BRANCH] = 3600
ROUTE_ISSUES[ISSUE466_BRANCH] = 466
TOTAL_LIMITS[ISSUE466_BRANCH] = 2000
ROUTE_ISSUES[ISSUE460_BRANCH] = 460
TOTAL_LIMITS[ISSUE460_BRANCH] = 2600
ROUTE_ISSUES[ISSUE368_BINDING_COMPAT_BRANCH] = 368
TOTAL_LIMITS[ISSUE368_BINDING_COMPAT_BRANCH] = 800
ROUTE_ISSUES[ISSUE368_AUTH_TRANSPORT_BRANCH] = 368
TOTAL_LIMITS[ISSUE368_AUTH_TRANSPORT_BRANCH] = 900
ROUTE_ISSUES[ISSUE368_TIMEOUT_BRANCH] = 368
TOTAL_LIMITS[ISSUE368_TIMEOUT_BRANCH] = 1220
ROUTE_ISSUES[ISSUE494_BRANCH] = 494
TOTAL_LIMITS[ISSUE494_BRANCH] = 1420
ROUTE_ISSUES[ISSUE498_BRANCH] = 498
TOTAL_LIMITS[ISSUE498_BRANCH] = 5200
ISSUE383_BINARY_FILES = {
    "frontend/public/demo/myra-synthetic-presenter.webp",
    "frontend/public/demo/raj-synthetic-presenter.webp",
}
ISSUE452_BYTE_LIMITS = {
    "docs/governance/schemas/cut1-human-realism-evaluation-v1.schema.json": 30_000,
    "docs/governance/schemas/cut1-presenter-provider-acceptance-v1.schema.json": 30_000,
    "scripts/quality/cut1_presenter_contract.py": 40_000,
    "tests/unit/test_cut1_presenter_contract.py": 30_000,
    "tests/unit/test_issue452_quality_dispatcher.py": 30_000,
}
ISSUE459_BYTE_LIMITS = {
    "docs/governance/preflights/issue-459.json": 32_000, "docs/governance/ISSUE_459_CONTROLLED_PRESENTER_PREFLIGHT_V1.md": 64_000, "docs/governance/schemas/cut1-controlled-presenter-evidence-v1.schema.json": 40_000,
    "docs/governance/cut1-controlled-presenter-red-corpus-v1.json": 48_000, "scripts/quality/cut1_controlled_presenter.py": 16_000, "tests/unit/test_cut1_controlled_presenter_red.py": 60_000, "tests/unit/test_issue459_quality_dispatcher.py": 24_000, "docs/reviews/ISSUE_459_ENTRY_GATE_REVIEW.md": 48_000, "docs/ADR/0068-cut1-controlled-presenter-controller.md": 32_000, ".gitleaksignore": 2_000, "scripts/ci/check_gitleaks_regression.py": 24_000, "tests/unit/test_gitleaks_regression.py": 32_000, "scripts/quality/check_stage8_docs.py": 48_000, "tests/unit/test_stage8_quality_gate.py": 40_000,
}
ISSUE459_T03_BYTE_LIMITS = {
    "frontend/public/demo/cut1/raj-waist-up.webp": 500_000,
    "frontend/public/demo/cut1/myra-waist-up.webp": 500_000,
}
ISSUE459_SOURCE_SHA256 = {
    "specs/001-grounded-walkthrough-script/spec.md": "cd16ea947a70271f60a5ce7086e577c1cc25f380baf9a338342bfafb522b8c35", "specs/001-grounded-walkthrough-script/plan.md": "166dd8021026eb334607d0dab290c2b121964bcb979e7e502b574f830b45dfd4", "specs/001-grounded-walkthrough-script/tasks.md": "9c244de820bf0df1c1d7d7e4c323e5317ba5818cb625f88165e675ce51817fdc", "docs/reviews/ISSUE_16_SPEC_KIT_REVIEW_CHECKPOINT.md": "14dbdeb898af240fd30d203e131be8c6e8e29c5803c82463c1b50dc4c8616877",
    ".specify/memory/constitution.md": "ebb0c16c8aa9d967e4c946f31ae600e6e45016bf5c3aa6f098ceac795cd142c2", "docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md": "2e864e044253a98ea10fdf6dde1ab32a026354aaa5c00cebe3b40756d653936e", "docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md": "14dbbb6f005d9887ad8ab90340bca9fdcc5fb969579ef3d03f69d5566d0616f8", "docs/ENTERPRISE_READINESS_REGISTER.md": "fd42d73871b62f48e018ced1eb5020ffcb53a62cdbdd53936b7c257c22940c1d",
    "docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md": "e358396e7be7ecee89539b1bfb9eb7eb4d331799dd41a64b4cfca4f74e22489b", "docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md": "7c041dfcca1e5f7e067744eaec18b1577df4be2cf391eb128b786bde7ca1521b", "docs/governance/cut1-all-presenter-acceptance-matrix-v1.json": "f61cef9f7731f4603778d1b6a3a9ccccd3682c8e0ad233c9370169320612b2f5", "docs/governance/cut1-presenter-live-binding-v2.json": "89199278feabfdcee21fffe4a9ad4d157dd7fc9a11a2529562876cb6ecc74702",
    "docs/governance/cut1-project-facts-v1.json": "cb50de12ce2debb3d52308892428b9711e5efb41fe2ad59b175563809e7d314b", "demo/stage8_seed_project.md": "49b75655ddbbe43145a35215069bce2751de66393b39eb68d69b584d7ecfcc5e", "docs/demo/PHASE_1_DEMO_SCRIPT.md": "3b071180d4723784d84f5005644fc5a2aa5ef6b6adb6f7caeba2de76d68be435", "backend/app/presenter_registry.json": "eb31a953b85ffaf2c43f54e4da7fb89eda740c724967a9301f726c6091ab01c2",
    "docs/PRD.md": "2cde5d9ec7d8e932b25f2fdf66d4dd11f49065b50078f16f59b6a65cbb7d720a", "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md": "0a3c14d0d61fbfaf5fe6dec0a7ca3a9412f1b1fd8aa458837f0c3b37b5570db3", "docs/ARCHITECTURE.md": "e7515ee96dce07e0d583e15984ea335b6f2499bfd8aa6e9f519bc4a830122fa4", "docs/API_CONTRACT.md": "910259f61acbbec4e3432c482d821fd56f2fe8b2073211c7ce112c3cd87405bf",
    "docs/DATA_MODEL.md": "f073c9bff26717233f23c6317b03736c02bee5952b88fa840767f79287b6ec09", "docs/SECURITY_AND_PRIVACY.md": "185fe98ffa0b12287b6e7e8a532fac89ffa7a29380db71f8dd6aa4d1b7bc4b62", "docs/OBSERVABILITY_AND_COST.md": "c77a0d4ea071e6ea364d9c1f4175361633d4d54962c7fc8d9527033e160d91c6", "docs/governance/cut1-blinded-human-evaluation-protocol-v1.json": "fa3759985141639185618fbc595057412dd8582f60ed97fc462b30b7548580b8", "docs/governance/cut1-provider-bakeoff-contract-v1.json": "1a3fd981644488203e8c7cc38fc0389092b23b579cce860c3d35a1ca7a1786db",
}
ISSUE459_EDITABLE_AUTHORITY_SHA256 = {
    "Issue #459": "dd03b171f25b0d249a79834f22674c728e539fa8b171a97b3a4728474e0039d5", "5449632582": "07b7cb91660a21ba0a70419ff07195a2532089a087d7a289806142dc81151fa0", "5449637037": "f236d2840a7ce35e074b6e370dcc706278772c47fa09b6c18b20a344b22fd1a0", "5449765467": "75882f1f3deb8dea77ab945cd58f0526b04644fb4cb208bcd50ddea29846bbe7", "5449822130": "48f86809e1032884d5576ceefde06d64785b486e1adae940fe32c2b6391e6cf3", "5451872197": "a5241954c115e6849da70401cc029cc4517f83a3629b043462a42becc6146e7d", "5452170084": "8c9297b3faf1d6894442017afef2ce58dcb3ec2a6ee6c3037be2024abb2d0fce", "5456406377": "dcbc20d52a6acb636463389f7a4996d79b7262f30209576e13522e3576782a7a", "5460884573": "6ef7158ffa8347defbed97b3c18a7ad0728cec02ff217b8a0984048fb44887ac", "5461065184": "33a87c363da666be77362291e338323b57311f78c5f1ed22155f619dbe9726fc", "5461070398": "66a28207adc9c9a0438a0d1012baf626561bfca0e6e6644d837328f08808cb1f",
}
ISSUE459_BASE_SOURCE_SHA256 = {"docs/STATUS.md": "9045b595ca1622680f621dffa4dff88435e2fde0d13e3c061ced7eb6df9ae8bf", "docs/TRACEABILITY.md": "e597069e3d6b765a9d68e5336ff9597d6d7b809e5ea6f316f22312ca71ea136a", "docs/QUALITY_GATES.md": "9f628d22ec62075e560ef478820cf094d923cdf1cfded56a512291c61f6e542b", "docs/REPOSITORY_GUARDRAILS.md": "04f8b405bc7ba9b615cc1d5d7e489bcbf643b9de4bfc9b331e5a60c38629e82f"}
TEXT_LIMITS = {
    ISSUE502_BRANCH: {
        "docs/governance/preflights/issue-502.json": 320,
        "frontend/Dockerfile": 360,
        ".github/workflows/security.yml": 80,
        "scripts/ci/docker-image-scan.sh": 360,
        "scripts/ci/check_container_scan_consensus.py": 320,
        "scripts/quality/stage8_node_security.py": 300,
        "scripts/quality/check_stage8_docs.py": 80,
        "scripts/quality/stage8_cut1_routes.py": 240,
        "tests/unit/test_frontend_container_runtime.py": 420,
        "tests/unit/test_stage8_node_security.py": 380,
        "tests/unit/test_container_scan_consensus.py": 360,
        "tests/unit/test_stage8_quality_gate.py": 160,
        "tests/unit/test_stage8_cut1_routes.py": 280,
        "docs/ADR/0077-frontend-musl-scratch-runtime.md": 220,
        "docs/SECURITY_AND_PRIVACY.md": 140,
        "docs/THIRD_PARTY_NOTICES.md": 100,
        "docs/QUALITY_GATES.md": 180,
        "docs/STAGE_ISSUE_PLAN.md": 120,
        "docs/STATUS.md": 120,
        "docs/TRACEABILITY.md": 120,
    },
    ISSUE479_BRANCH: {
        "docs/governance/preflights/issue-479.json": 220,
        "backend/app/cut1_listening.py": 620, "tests/unit/test_cut1_listening.py": 530,
        "scripts/quality/stage8_cut1_routes.py": 160,
        "tests/unit/test_stage8_cut1_routes.py": 260,
        "tests/unit/test_stage8_quality_gate.py": 60,
        "docs/ADR/0073-cut1-exact-hash-listening-authority.md": 140,
        "docs/API_CONTRACT.md": 80, "docs/DATA_MODEL.md": 80,
        "docs/SECURITY_AND_PRIVACY.md": 80, "docs/OBSERVABILITY_AND_COST.md": 60,
        "docs/QUALITY_GATES.md": 80, "docs/STAGE_ISSUE_PLAN.md": 80,
        "docs/STATUS.md": 100, "docs/TRACEABILITY.md": 50,
    },
    ISSUE482_BRANCH: {
        "docs/governance/preflights/issue-482.json": 220, "uv.lock": 1800,
        "tests/unit/test_dependency_security_contract.py": 240,
        "scripts/quality/stage8_cut1_routes.py": 140,
        "tests/unit/test_stage8_cut1_routes.py": 220,
        "tests/unit/test_stage8_quality_gate.py": 40,
        "docs/THIRD_PARTY_NOTICES.md": 100, "docs/QUALITY_GATES.md": 80,
        "docs/STAGE_ISSUE_PLAN.md": 80, "docs/STATUS.md": 100,
        "docs/TRACEABILITY.md": 60,
    },
    ISSUE495_BRANCH: {
        "frontend/package-lock.json": 120,
        "docs/governance/preflights/issue-495-browserslist-security-refresh.json": 220,
        "scripts/quality/stage8_cut1_routes.py": 120,
        "tests/unit/test_stage8_cut1_routes.py": 160,
        "tests/unit/test_dependency_security_contract.py": 180,
        "tests/unit/test_frontend_dependency_security_contract.py": 140,
        "docs/ADR/0074-browserslist-4-28-8-security-refresh.md": 160,
        "docs/STATUS.md": 80,
        "docs/TRACEABILITY.md": 80,
    },
    ISSUE499_BRANCH: {
        "docs/governance/preflights/issue-499-pypdf-6-16-2-security-refresh.json": 220,
        "pyproject.toml": 20,
        "uv.lock": 100,
        "scripts/quality/stage8_cut1_routes.py": 120,
        "tests/unit/test_stage8_cut1_routes.py": 140,
        "tests/unit/test_dependency_security_contract.py": 220,
        "docs/ADR/0075-pypdf-6-16-2-security-refresh.md": 80,
        "docs/STATUS.md": 40,
        "docs/THIRD_PARTY_NOTICES.md": 40,
        "docs/TRACEABILITY.md": 20,
    },
    ISSUE478_BRANCH: {
        "docs/STATUS.md": 100,
        "docs/governance/preflights/issue-478.json": 220,
        "scripts/quality/stage8_cut1_routes.py": 180,
        "tests/unit/test_stage8_cut1_routes.py": 240,
        "tests/unit/test_stage8_quality_gate.py": 60,
    },
    ISSUE475_BRANCH: {
        "backend/app/cut1_audio.py": 340,
        "tests/unit/test_cut1_audio.py": 600,
        "docs/governance/preflights/issue-475.json": 260,
        "scripts/quality/stage8_cut1_routes.py": 160,
        "tests/unit/test_stage8_cut1_routes.py": 240,
        "tests/unit/test_stage8_quality_gate.py": 40,
        "docs/ADR/0071-cut1-audio-caption-authority.md": 120,
        "docs/API_CONTRACT.md": 60,
        "docs/DATA_MODEL.md": 80,
        "docs/SECURITY_AND_PRIVACY.md": 80,
        "docs/QUALITY_GATES.md": 100,
        "docs/STATUS.md": 100,
        "docs/TRACEABILITY.md": 100,
    },
    ISSUE468_BRANCH: {
        "AGENTS.md": 70,
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": 180,
        "docs/governance/preflights/issue-468-scoped-merge-cleanup.json": 260,
        "docs/STATUS.md": 90,
        "docs/agent-context/context-policy-manifest-v1.json": 200,
        "scripts/quality/check_stage8_docs.py": 80,
        "scripts/quality/stage8_cut1_routes.py": 180,
        "tests/unit/test_stage8_quality_gate.py": 160,
        "tests/unit/test_stage8_cut1_routes.py": 220,
    },
    ISSUE486_BRANCH: {
        "docs/governance/preflights/issue-486-reviewer-impact-summary.json": 320,
        ".github/pull_request_template.md": 100,
        "scripts/guardrails_check.py": 360,
        "tests/unit/test_guardrails_check.py": 480,
        "scripts/quality/stage8_cut1_routes.py": 260,
        "tests/unit/test_stage8_cut1_routes.py": 320,
        "docs/REPOSITORY_GUARDRAILS.md": 120,
        "docs/QUALITY_GATES.md": 120,
        "docs/agent-context/context-policy-manifest-v1.json": 40,
        "docs/STATUS.md": 100,
    },
    ISSUE486_PROTECTED_BRANCH: {
        "AGENTS.md": 40,
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": 40,
        "docs/agent-context/context-policy-manifest-v1.json": 50,
        "docs/governance/preflights/issue-486-protected-reviewer-impact.json": 260,
        "docs/STATUS.md": 20,
        "scripts/quality/stage8_cut1_routes.py": 80,
        "tests/unit/test_stage8_cut1_routes.py": 160,
    },
    ISSUE486_HASH_CLEANUP_BRANCH: {
        "scripts/guardrails_check.py": 40,
        "tests/unit/test_guardrails_check.py": 120,
        "docs/governance/preflights/issue-486-protected-hash-cleanup.json": 220,
        "docs/STATUS.md": 20,
        "scripts/quality/stage8_cut1_routes.py": 80,
        "tests/unit/test_stage8_cut1_routes.py": 180,
    },
    ISSUE466_BRANCH: {
        "docs/governance/preflights/issue-466.json": 320,
        "docs/governance/cut1-project-facts-v1.json": 220,
        "backend/app/cut1_grounding.py": 320,
        "tests/unit/test_cut1_atomic_grounding.py": 520,
        "tests/unit/test_cut1_narration.py": 240,
        "docs/ADR/0072-cut1-presenter-source-integrity.md": 220,
        "scripts/quality/stage8_cut1_routes.py": 140,
        "tests/unit/test_stage8_cut1_routes.py": 240,
        "tests/unit/test_stage8_quality_gate.py": 40,
        "docs/QUALITY_GATES.md": 120,
        "docs/STAGE_ISSUE_PLAN.md": 120,
        "docs/STATUS.md": 180,
        "docs/TRACEABILITY.md": 120,
    },
    ISSUE471_BRANCH: {
        "docs/governance/preflights/issue-471-cleanup-authority-anchor.json": 240,
        "docs/STATUS.md": 100,
        "scripts/guardrails_check.py": 260, "tests/unit/test_guardrails_check.py": 360,
        "scripts/quality/stage8_cut1_routes.py": 180, "tests/unit/test_stage8_cut1_routes.py": 260,
    },
    ISSUE473_BRANCH: {
        "tests/unit/test_guardrails_check.py": 80,
        "docs/governance/preflights/issue-473-cleanup-anchor-consumer.json": 180,
        "scripts/quality/stage8_cut1_routes.py": 100,
        "tests/unit/test_stage8_cut1_routes.py": 140,
        "docs/STATUS.md": 80,
    },
    ISSUE459_T05B_BRANCH: {path: 3600 for path in ROUTES[ISSUE459_T05B_BRANCH]},
    ISSUE459_T05A_BRANCH: {
        "docs/governance/preflights/issue-459-t05a.json": 180,
        "backend/app/cut1_grounding.py": 120, "backend/app/narration.py": 180,
        "tests/unit/test_cut1_atomic_grounding.py": 260,
        "tests/unit/test_cut1_narration.py": 240,
        "docs/ADR/0070-cut1-t05-grounded-narration-handoff.md": 180,
        "scripts/quality/stage8_cut1_routes.py": 180,
        "tests/unit/test_stage8_cut1_routes.py": 320,
        "docs/QUALITY_GATES.md": 100, "docs/STAGE_ISSUE_PLAN.md": 120,
        "docs/STATUS.md": 120, "docs/TRACEABILITY.md": 100,
    },
    ISSUE459_T03_BRANCH: {
        "pyproject.toml": 20, "uv.lock": 200,
        "docs/governance/preflights/issue-459-t03.json": 220,
        "docs/governance/cut1-presenter-derivatives-v1.json": 420,
        "backend/app/presenter_registry.py": 500,
        "tests/unit/test_cut1_presenter_derivatives.py": 700,
        "tests/unit/test_dependency_security_contract.py": 220,
        "docs/ADR/0069-cut1-presenter-derivative-readiness-binding.md": 180,
        "docs/THIRD_PARTY_NOTICES.md": 260,
        "scripts/quality/stage8_cut1_routes.py": 220,
        "tests/unit/test_stage8_cut1_routes.py": 340,
        "docs/QUALITY_GATES.md": 120, "docs/STAGE_ISSUE_PLAN.md": 120,
        "docs/STATUS.md": 160, "docs/TRACEABILITY.md": 120,
    },
    ISSUE459_BRANCH: {
        "docs/governance/preflights/issue-459.json": 220, "docs/governance/ISSUE_459_CONTROLLED_PRESENTER_PREFLIGHT_V1.md": 850, "docs/governance/schemas/cut1-controlled-presenter-evidence-v1.schema.json": 450, "docs/governance/cut1-controlled-presenter-red-corpus-v1.json": 500,
        "scripts/quality/cut1_controlled_presenter.py": 140, "tests/unit/test_cut1_controlled_presenter_red.py": 700, "scripts/quality/check_quality_stage.py": 60, "tests/unit/test_issue459_quality_dispatcher.py": 140, "scripts/quality/stage8_cut1_routes.py": 180, "tests/unit/test_stage8_cut1_routes.py": 340,
        "docs/reviews/ISSUE_459_ENTRY_GATE_REVIEW.md": 500, "docs/QUALITY_GATES.md": 120, "docs/STAGE_ISSUE_PLAN.md": 120, "docs/PHASE_PLAN.md": 100, "docs/STATUS.md": 160, "docs/TRACEABILITY.md": 120, "backend/app/cut1_controlled_presenter.py": 900, "tests/unit/test_cut1_controlled_presenter.py": 900, "docs/ADR/0068-cut1-controlled-presenter-controller.md": 260, ".gitleaksignore": 20, "scripts/ci/check_gitleaks_regression.py": 220, "tests/unit/test_gitleaks_regression.py": 260, "scripts/quality/check_stage8_docs.py": 60, "tests/unit/test_stage8_quality_gate.py": 100,
    },
    ISSUE460_BRANCH: {
        "docs/governance/preflights/issue-460.json": 180, "docs/ADR/0069-semgrep-1-175-override-removal.md": 180,
        "docs/RELEASE_CHECKLIST.md": 80, "docs/RISK_REGISTER.md": 80, "docs/SECURITY_AND_PRIVACY.md": 80,
        "scripts/ci/check_semgrep_security.py": 220, "tools/semgrep/pyproject.toml": 20,
        "tools/semgrep/reviewed-inputs.sha256": 20, "tools/semgrep/uv.lock": 500,
        "scripts/quality/stage8_cut1_routes.py": 180, "tests/unit/test_stage8_cut1_routes.py": 300,
        "tests/unit/test_dependency_security_contract.py": 250, "docs/QUALITY_GATES.md": 80,
        "docs/STAGE_ISSUE_PLAN.md": 80, "docs/STATUS.md": 80, "docs/THIRD_PARTY_NOTICES.md": 80,
        "docs/TRACEABILITY.md": 80,
        "scripts/quality/check_issue16_spec_kit.py": 420,
        "tests/unit/test_issue16_spec_kit_gate.py": 500,
        "tests/unit/test_issue427_architecture_reset.py": 80,
        "tests/unit/test_stage8_quality_gate.py": 80,
        ".gitleaksignore": 20,
        "scripts/ci/check_gitleaks_regression.py": 220,
        "scripts/ci/dependency-security.sh": 80,
        "tests/unit/test_gitleaks_regression.py": 260,
    },
    ISSUE452_BRANCH: {
        "docs/governance/preflights/issue-452.json": 260,
        "docs/governance/schemas/cut1-human-realism-evaluation-v1.schema.json": 360,
        "docs/governance/schemas/cut1-presenter-provider-acceptance-v1.schema.json": 400,
        "docs/governance/cut1-blinded-human-evaluation-protocol-v1.json": 300,
        "docs/governance/cut1-all-presenter-acceptance-matrix-v1.json": 300,
        "docs/governance/cut1-provider-bakeoff-contract-v1.json": 360,
        "docs/governance/cut1-presenter-contract-red-freeze-v1.json": 220,
        "scripts/quality/cut1_presenter_contract.py": 480,
        "tests/unit/test_cut1_presenter_contract.py": 450,
        "scripts/quality/check_quality_stage.py": 50,
        "tests/unit/test_issue452_quality_dispatcher.py": 120,
        "tests/unit/test_quality_dispatcher.py": 100,
        "scripts/quality/stage8_cut1_routes.py": 160,
        "tests/unit/test_stage8_cut1_routes.py": 240,
        "docs/ADR/0065-cut1-all-presenter-acceptance-provider-bakeoff.md": 240,
        "docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md": 100,
        "docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md": 120,
        "docs/ENTERPRISE_READINESS_REGISTER.md": 100,
        "docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md": 100,
        "docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md": 120,
        "docs/QUALITY_GATES.md": 100,
        "docs/STATUS.md": 120,
        "docs/THIRD_PARTY_NOTICES.md": 100,
        "docs/TRACEABILITY.md": 100,
    },
    ISSUE451_BRANCH: {
        "docs/PHASE_PLAN.md": 120,
        "docs/STATUS.md": 180,
        "scripts/quality/stage8_cut1_routes.py": 100,
        "tests/unit/test_adversarial_convergence.py": 20,
        "tests/unit/test_guardrails_check.py": 20,
        "tests/unit/test_stage8_cut1_routes.py": 120,
        "docs/QUALITY_GATES.md": 80,
        "docs/STAGE_ISSUE_PLAN.md": 80,
    },
    ISSUE150_BRANCH: {
        path: 180 if path.endswith("issue-150.json")
        else 150 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py"}
        else 120 if path.startswith("tests/unit/") or path.endswith("issue-428.json")
        else 100
        for path in ROUTES[ISSUE150_BRANCH]
    },
    ISSUE424_BRANCH: {
        path: {
            "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md": 5000,
            "docs/governance/narratwin-master-program-v1.json": 180,
            "docs/governance/preflights/issue-424.json": 500,
            "docs/reviews/ISSUE_424_EXECUTION_SPEC_REVIEW.md": 500,
            "docs/reviews/ISSUE_424_CUT1_FALSE_SUCCESS_REVIEW.md": 500,
            "docs/reviews/ISSUE_424_PLATFORM_SECURITY_LEARNING_REVIEW.md": 500,
            "docs/ADR/0059-master-program-authority-and-route-bootstrap.md": 400,
            "docs/STAGE_ISSUE_PLAN.md": 250,
            "docs/STATUS.md": 250,
            "docs/TRACEABILITY.md": 250,
            "scripts/quality/stage8_cut1_routes.py": 300,
            "tests/unit/test_stage8_cut1_routes.py": 320,
            "scripts/guardrails_check.py": 100,
            "tests/unit/test_guardrails_check.py": 180,
        }[path]
        for path in ROUTES[ISSUE424_BRANCH]
    },
    ISSUE421_BRANCH: {
        path: {
            "docs/governance/preflights/issue-421.json": 500,
            "docs/governance/cut1-project-facts-v1.json": 600,
            "backend/app/narration.py": 160,
            "backend/app/cut1_grounding.py": 900,
            "backend/app/rag/models.py": 180,
            "backend/app/stage4.py": 600,
            "backend/app/evaluation_lineage.py": 300,
            "tests/unit/test_cut1_atomic_grounding.py": 1200,
            "tests/unit/test_cut1_narration.py": 500,
            "tests/unit/test_evaluation_lineage.py": 400,
            "scripts/quality/stage8_cut1_routes.py": 180,
            "tests/unit/test_stage8_cut1_routes.py": 300,
            "docs/ADR/0058-cut1-atomic-project-facts-grounding.md": 320,
            "docs/API_CONTRACT.md": 180,
            "docs/DATA_MODEL.md": 180,
            "docs/SECURITY_AND_PRIVACY.md": 220,
            "docs/OBSERVABILITY_AND_COST.md": 180,
            "docs/QUALITY_GATES.md": 180,
            "docs/STAGE_ISSUE_PLAN.md": 180,
            "docs/STATUS.md": 220,
            "docs/TRACEABILITY.md": 220,
        }[path]
        for path in ROUTES[ISSUE421_BRANCH]
    },
    ISSUE415_BRANCH: {path: 1200 if path == "scripts/quality/pr_body_consistency.py" else 900 if path == "tests/unit/test_pr_body_consistency.py" else 400 if path in {"scripts/quality/pr_body_consistency_cli.py", ".github/workflows/pr-body-consistency.yml"} else 250 for path in ROUTES[ISSUE415_BRANCH]},
    ISSUE415_CORRECTION_BRANCH: {path: 250 for path in ROUTES[ISSUE415_CORRECTION_BRANCH]},
    ISSUE413_BRANCH: {
        path: 700 if path in {"scripts/ci/docker-image-scan.sh", "tests/unit/test_container_scan_consensus.py"}
        else 500 if path in {"scripts/ci/check_container_scan_consensus.py", "tests/unit/test_stage8_quality_gate.py"}
        else 350 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py"}
        else 400 if path == "tests/unit/test_stage8_node_security.py"
        else 300 if path == "scripts/quality/stage8_node_security.py"
        else 80 if path == "scripts/quality/check_stage8_docs.py"
        else 300 if path in {"frontend/Dockerfile", "tests/unit/test_frontend_container_runtime.py",
                             "docs/governance/preflights/issue-413.json"}
        else 220
        for path in ROUTES[ISSUE413_BRANCH]
    },
    ISSUE368_ADAPTER_BRANCH: {
        path: 1700 if path == "backend/app/tts_provider.py"
        else 1200 if path == "tests/unit/test_stage6_tts_provider.py"
        else 600 if path in {"backend/app/narration.py", "backend/app/stage6.py",
                             "tests/unit/test_cut1_narration.py", "tests/unit/test_stage6_multilingual.py"}
        else 400 if path in {"tests/api/test_stage6_multilingual_api.py",
                             "scripts/quality/stage8_cut1_routes.py",
                             "tests/unit/test_stage8_cut1_routes.py"}
        else 300 if path == "docs/governance/preflights/issue-368.json" else 240
        for path in ROUTES[ISSUE368_ADAPTER_BRANCH]
    },
    ISSUE368_IMPLEMENTATION_BRANCH: {
        path: {
            "docs/governance/preflights/issue-368.json": 240,
            "backend/app/google_tts_runtime.py": 700,
            "backend/app/tts_provider.py": 220,
            "pyproject.toml": 20,
            "uv.lock": 300,
            "tests/unit/test_google_tts_runtime.py": 800,
            "tests/unit/test_dependency_security_contract.py": 220,
            "scripts/quality/stage8_cut1_routes.py": 60,
            "tests/unit/test_stage8_cut1_routes.py": 160,
            "docs/ADR/0056-cut1-google-gemini-tts.md": 180,
            "docs/ARCHITECTURE.md": 70,
            "docs/OBSERVABILITY_AND_COST.md": 70,
            "docs/QUALITY_GATES.md": 70,
            "docs/SECURITY_AND_PRIVACY.md": 100,
            "docs/STAGE_ISSUE_PLAN.md": 100,
            "docs/STATUS.md": 120,
            "docs/THIRD_PARTY_NOTICES.md": 150,
            "docs/TRACEABILITY.md": 220,
        }[path]
        for path in ROUTES[ISSUE368_IMPLEMENTATION_BRANCH]
    },
    ISSUE368_QUOTA_FIX_BRANCH: {
        path: {
            "backend/app/google_tts_runtime.py": 500,
            "backend/app/tts_provider.py": 500,
            "tests/unit/test_google_tts_runtime.py": 600,
            "tests/unit/test_stage6_tts_provider.py": 800,
            "docs/governance/preflights/issue-368.json": 500,
            "scripts/quality/stage8_cut1_routes.py": 160,
            "tests/unit/test_stage8_cut1_routes.py": 260,
            "docs/ADR/0056-cut1-google-gemini-tts.md": 240,
            "docs/API_CONTRACT.md": 160,
            "docs/DATA_MODEL.md": 160,
            "docs/SECURITY_AND_PRIVACY.md": 220,
            "docs/OBSERVABILITY_AND_COST.md": 180,
            "docs/STATUS.md": 220,
            "docs/TRACEABILITY.md": 220,
            "scripts/ci/verify_branch_protection.py": 80,
            "tests/unit/test_branch_protection_verifier.py": 220,
            "tests/unit/test_governance_preflight_github.py": 80,
            "docs/REPOSITORY_GUARDRAILS.md": 80,
            "docs/agent-context/context-policy-manifest-v1.json": 10,
        }[path]
        for path in ROUTES[ISSUE368_QUOTA_FIX_BRANCH]
    },
    ISSUE368_BINDING_COMPAT_BRANCH: {
        "backend/app/tts_provider.py": 20,
        "tests/unit/test_stage6_tts_provider.py": 30,
        "docs/governance/preflights/issue-368-provider-binding-compat.json": 200,
        "scripts/quality/stage8_cut1_routes.py": 130,
        "tests/unit/test_stage8_cut1_routes.py": 170,
        "docs/STATUS.md": 100,
        "docs/ADR/0056-cut1-google-gemini-tts.md": 60,
        "docs/TRACEABILITY.md": 80,
    },
    ISSUE368_AUTH_TRANSPORT_BRANCH: {
        "backend/app/google_tts_runtime.py": 20,
        "tests/unit/test_google_tts_runtime.py": 80,
        "docs/governance/preflights/issue-368-auth-transport.json": 220,
        "scripts/quality/stage8_cut1_routes.py": 140,
        "tests/unit/test_stage8_cut1_routes.py": 200,
        "docs/STATUS.md": 100,
        "docs/ADR/0056-cut1-google-gemini-tts.md": 60,
        "docs/TRACEABILITY.md": 80,
    },
    ISSUE368_TIMEOUT_BRANCH: {
        "backend/app/google_tts_runtime.py": 40,
        "backend/app/tts_provider.py": 40,
        "tests/unit/test_google_tts_runtime.py": 100,
        "tests/unit/test_stage6_tts_provider.py": 120,
        "docs/governance/preflights/issue-368-google-tts-timeout.json": 260,
        "scripts/quality/stage8_cut1_routes.py": 160,
        "tests/unit/test_stage8_cut1_routes.py": 220,
        "docs/STATUS.md": 100,
        "docs/ADR/0056-cut1-google-gemini-tts.md": 100,
        "docs/TRACEABILITY.md": 80,
    },
    ISSUE494_BRANCH: {
        "backend/app/tts_provider.py": 180,
        "tests/unit/test_stage6_tts_provider.py": 260,
        "docs/governance/preflights/issue-494-google-tts-failure-diagnostics.json": 260,
        "scripts/quality/stage8_cut1_routes.py": 160,
        "tests/unit/test_stage8_cut1_routes.py": 220,
        "docs/STATUS.md": 120,
        "docs/ADR/0056-cut1-google-gemini-tts.md": 120,
        "docs/TRACEABILITY.md": 100,
    },
    ISSUE498_BRANCH: {
        "backend/app/google_tts_runtime.py": 650,
        "backend/app/tts_provider.py": 350,
        "tests/unit/test_google_tts_runtime.py": 850,
        "tests/unit/test_stage6_tts_provider.py": 450,
        "tests/unit/test_dependency_security_contract.py": 500,
        "pyproject.toml": 10,
        "uv.lock": 1000,
        "docs/governance/preflights/issue-498-google-tts-official-grpc.json": 340,
        "scripts/quality/stage8_cut1_routes.py": 240,
        "tests/unit/test_stage8_cut1_routes.py": 320,
        "docs/ADR/0056-cut1-google-gemini-tts.md": 180,
        "docs/STATUS.md": 140,
        "docs/THIRD_PARTY_NOTICES.md": 180,
        "docs/TRACEABILITY.md": 140,
    },
    ISSUE368_PROMPT_BRANCH: {
        path: 260 if path == "tests/unit/test_stage8_cut1_routes.py"
        else 180 if path == "docs/governance/preflights/issue-368.json"
        else 140 if path in {
            "docs/governance/cut1-google-gemini-tts-style-prompts-v1.json",
            "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md",
        }
        else 100 if path == "scripts/quality/stage8_cut1_routes.py" else 60
        for path in ROUTES[ISSUE368_PROMPT_BRANCH]
    },
    ISSUE368_BRANCH: {
        path: 1200 if path == "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md"
        else 500 if path == "docs/ADR/0056-cut1-google-gemini-tts.md"
        else 300 if path == "docs/governance/preflights/issue-368.json"
        else 220 if path in {"docs/SECURITY_AND_PRIVACY.md", "docs/OBSERVABILITY_AND_COST.md",
                             "tests/unit/test_stage8_cut1_routes.py"}
        else 180 if path == "scripts/quality/stage8_cut1_routes.py" else 160
        for path in ROUTES[ISSUE368_BRANCH]
    },
    ISSUE382_BRANCH: {
        path: 220 if path.endswith("issue-382.json") or path.startswith("docs/ADR/0055-")
        else 750 if path == "backend/app/narration.py"
        else 900 if path == "tests/unit/test_cut1_narration.py"
        else 120 for path in ROUTES[ISSUE382_BRANCH]
    },
    ISSUE405_BRANCH: {
        path: 220 if path.endswith("issue-405.json") else 160
        for path in ROUTES[ISSUE405_BRANCH]
    },
    ISSUE403_BRANCH: {
        path: 180 if path.endswith("issue-403.json")
        else 110 if path == "tests/unit/test_frontend_dependency_security_contract.py"
        else 80 if path in {"scripts/ci/check_container_scan_consensus.py",
                            "tests/unit/test_container_scan_consensus.py"}
        else 70 if path == "scripts/quality/stage8_cut1_routes.py"
        else 60 if path.startswith("docs/ADR/") else 40
        for path in ROUTES[ISSUE403_BRANCH]
    },
    ISSUE428_BRANCH: {
        path: 150 if path.endswith("issue-428.json") else 110
        if path == "tests/unit/test_frontend_dependency_security_contract.py" else 70
        for path in ROUTES[ISSUE428_BRANCH]
    },
    ISSUE401_BRANCH: {
        path: 190 if path.endswith("issue-401.json")
        else 100 if path.startswith("tests/unit/")
        else 80 if path == "scripts/quality/stage8_cut1_routes.py"
        else 60 if path.startswith("docs/ADR/") else 40
        for path in ROUTES[ISSUE401_BRANCH]
    },
    ISSUE396_BRANCH: {
        path: 180 if path.endswith("issue-396.json") else 80 if path.startswith("tests/unit/") else 40
        for path in ROUTES[ISSUE396_BRANCH]
    },
    ISSUE386_BRANCH: {
        path: 300 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py"}
        else 120 if path == "tests/acceptance/test_issue280_local_e2e_demo.py"
        else 20 if path == "tests/unit/test_stage8_quality_gate.py"
        else 80 if path == "scripts/quality/check_stage8_docs.py" else 120
        for path in ROUTES[ISSUE386_BRANCH]
    },
    ISSUE385_BRANCH: {
        path: 120 if path == "tests/acceptance/test_issue280_local_e2e_demo.py" else 100
        for path in ROUTES[ISSUE385_BRANCH]
    },
    ISSUE384_BRANCH: {
        path: 10 if path == "scripts/quality/check_stage8_docs.py"
        else 20 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py"}
        else 160 for path in ROUTES[ISSUE384_BRANCH]
    },
    ISSUE383_BRANCH: {
        path: 260 if path == "tests/unit/test_cut1_presenter_assets.py" else 160
        for path in ROUTES[ISSUE383_BRANCH] - ISSUE383_BINARY_FILES
    },
    ISSUE367_BRANCH: {
        path: 500 if path in {"backend/app/presenter_registry.py",
                              "tests/unit/test_cut1_presenter_registry.py"}
        else 260 if path == "backend/app/presenter_registry.json"
        else 220 if path in {"docs/governance/preflights/issue-367.json",
                             "docs/ADR/0054-cut1-presenter-registry.md"}
        else 180 if path in {"scripts/quality/stage8_cut1_routes.py",
                             "tests/unit/test_stage8_cut1_routes.py"}
        else 120 for path in ROUTES[ISSUE367_BRANCH]
    },
    ISSUE397_BRANCH: {
        path: 160 if path in {"docs/governance/preflights/issue-397.json",
                             "tests/unit/test_guardrails_check.py"}
        else 100 if path == "scripts/guardrails_check.py"
        else 10 if path == "docs/agent-context/context-policy-manifest-v1.json" else 80
        for path in ROUTES[ISSUE397_BRANCH]
    },
    ISSUE393_BRANCH: {
        path: 180 if path.endswith(("issue-393.json", "issue-396.json"))
        else 160 if path == "tests/unit/test_stage8_quality_gate.py"
        else 80 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
                            "tests/unit/test_dependency_security_contract.py",
                            "scripts/ci/check_container_scan_consensus.py",
                            "tests/unit/test_container_scan_consensus.py"} else 40
        for path in ROUTES[ISSUE393_BRANCH]
    },
}


ISSUE424_HEADINGS = (
    "1. Purpose, claims, and execution authority",
    "2. Capability and evidence classification",
    "3. Stale-plan and route enforcement",
    "4. Cut1AuthorityManifestV1",
    "5. Planning and delivery layers",
    "6. Roles and separation of duties",
    "7. Intended-versus-implemented baseline",
    "8. Architecture and living documentation",
    "9. Project requirements intake",
    "10. Composition and provider resolution",
    "11. Provider-neutral contracts",
    "12. Credentials and BYOK",
    "13. Provider governance",
    "14. Provider switching and migration",
    "15. Product AI workflow",
    "16. RAG and knowledge portability",
    "17. Run lineage",
    "18. Observability and NFR controls",
    "19. Controlled feedback and learning",
    "20. Serialized Cut 1 route",
    "21. Canonical Meera narration and audio",
    "22. Meera asset authority",
    "23. Media calibration",
    "24. Renderer prequalification",
    "25. Audition fixture and scoring",
    "26. Winner lock",
    "27. PaidOperationV1",
    "28. ArtifactStore and MediaValidator",
    "29. Cut1VisualArtifactAcceptanceV1",
    "30. Independent full renders",
    "31. Captions",
    "32. Cut1RealMediaAcceptanceV1",
    "33. Disclosure policy",
    "34. UI and browser acceptance",
    "35. Required negative tests",
    "36. Task resource ledger",
    "37. Docker, temporary-file, and process hygiene",
    "38. Git, main synchronization, and branch cleanup",
    "39. End-of-process closeout verification",
    "40. Mandatory plain-English handoff",
    "41. Completion claims",
    "42. Final pre-log review gate",
)
ISSUE424_CONTROLLER_SHA256 = "c3e3c85bb980aab4f818e80be3db5484e564423d77bc3ab6e81ba736c3af3420"
ISSUE424_CONTROLLER_BYTES = 40135
ISSUE424_CONTROLLER_LINES = 887
ISSUE424_CONTROLLER_HAS_TRAILING_NEWLINE = True
ISSUE424_BINDING_FIELDS = {
    "schemaVersion", "controllerId", "controllerIssue", "bootstrapBranch", "acceptedBaseSha",
    "documentPath", "documentSha256", "documentBytes", "documentLines", "hasTrailingNewline",
    "numberedSections", "firstNumberedSection", "lastNumberedSection", "proposalState",
    "implementationAuthority", "activeProgramRoute", "requiredReviews", "requiredApprovals",
    "predecessor", "authorityTransition", "prohibitedClaims", "routeActivationGuard",
}
ISSUE424_REVIEWS = [
    {"id": "execution-specification", "artifact": "docs/reviews/ISSUE_424_EXECUTION_SPEC_REVIEW.md",
     "state": "PENDING_INDEPENDENT_REVIEW"},
    {"id": "cut1-false-success-media", "artifact": "docs/reviews/ISSUE_424_CUT1_FALSE_SUCCESS_REVIEW.md",
     "state": "PENDING_INDEPENDENT_REVIEW"},
    {"id": "platform-security-learning", "artifact": "docs/reviews/ISSUE_424_PLATFORM_SECURITY_LEARNING_REVIEW.md",
     "state": "PENDING_INDEPENDENT_REVIEW"},
]
ISSUE424_APPROVALS = {
    "ownerExactBytes": "PENDING", "eligibleNonAuthorExactHead": "PENDING",
    "referenceOnlyMergeWording": "PENDING",
}
ISSUE424_TRANSITION = {
    "decisionSchemaVersion": "MasterProgramAuthorityDecisionV1",
    "decisionPath": "docs/governance/narratwin-master-program-authority-decision-v1.json",
    "createdBy": "separately-governed authority-reconciliation-and-stale-route-enforcement child",
    "requiredDecisionStateForActivation": "ACCEPTED",
    "requiredEvidence": [
        "controllerProposalSha256", "exactHeadSha", "ownerExactBytesApproval",
        "independentReviewDispositions", "eligibleNonAuthorApproval", "mergeSha",
        "mergedMainChecks", "statusReconciliation", "issueDisposition", "authorityState",
        "verificationState", "expiryOrRevalidation",
    ],
    "routeActivationFromProposal": "PROHIBITED",
}
ISSUE424_PREDECESSOR = {
    "issue": 421, "pullRequest": 422,
    "reviewedHeadSha": "f68c87c6e82715a903666db13a39131b806837c7",
    "mergeSha": ISSUE424_BASE,
    "treeSha": "9c5aa188c84757db9b2c851fc11ab77d503200fe",
    "mergedMainRun": 31593554541, "mergedMainRunConclusion": "SUCCESS",
    "issueDisposition": "CLOSED_COMPLETED",
}
ISSUE424_PROHIBITED_CLAIMS = [
    "Cut1DemoCompleteV1", "CUT1_REAL_MEDIA_ACCEPTED", "full plug-and-play",
    "hosted operation", "production durability", "production readiness",
    "public availability", "release",
]
ISSUE424_ROUTE_GUARD = (
    "This proposal never grants execution authority. A current ACCEPTED "
    "MasterProgramAuthorityDecisionV1 created by the separately governed "
    "authority-reconciliation and stale-route-enforcement child is required before any "
    "implementation route may activate."
)


class DuplicateJsonMember(ValueError):
    """Reject authority bytes whose meaning depends on parser key precedence."""


def load_json_without_duplicate_members(path: Path) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateJsonMember(key)
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
    )


def markdown_heading_body(text: str, heading: str, level: int) -> str:
    prefix = "#" * level
    pattern = rf"^{prefix} {re.escape(heading)}\s*\n(?P<body>.*?)(?=^#{{1,{level}}} |\Z)"
    match = re.search(pattern, text, flags=re.M | re.S)
    return match.group("body") if match else ""


def operative_markdown_text(document: str) -> str:
    without_comments = re.sub(r"<!--.*?-->", "", document, flags=re.S)
    operative: list[str] = []
    fence: str | None = None
    for line in without_comments.splitlines():
        marker = re.match(r"^\s*(```|~~~)", line)
        if marker:
            if fence is None:
                fence = marker.group(1)
            elif fence == marker.group(1):
                fence = None
            continue
        if fence is None:
            operative.append(line)
    return "\n".join(operative)


def has_unsafe_broad_prune_authorization(document: str) -> bool:
    operative = unicodedata.normalize("NFKC", operative_markdown_text(document))
    if any(unicodedata.category(char) == "Cf" or (char.isalpha() and not char.isascii()) for char in operative):
        return True
    normalized = re.sub(r"\s+", " ", operative.lower())
    safe_clauses = (
        "prohibit broad prune operations;",
        "do not run broad prune operations, including docker system, image, builder, volume, network, cache, "
        "worktree, branch, or recursive filesystem pruning; broad prune operations are prohibited even when "
        "every cleanup target has asserted ownership",
    )
    for clause in safe_clauses:
        normalized = normalized.replace(clause, "", 1)
    return "broad" in normalized and "prun" in normalized


def merge_cleanup_contract_failures(
    root: Path,
    reader: Callable[[str], str] | None = None,
) -> list[str]:
    read_document = reader or (
        lambda path: (root / path).read_text(encoding="utf-8")
    )
    specifications = (
        (
            "AGENTS.md", "Non-Negotiable Workflow", 2,
            (
                "resolve scoped resource ownership before deletion",
                "prohibit broad prune operations",
                "before-and-after hashes and status counts",
                "main...origin/main is 0 ahead / 0 behind",
                "retained, deleted, and recoverability report",
                "proof of absence",
            ),
        ),
        (
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
            "Mandatory Merge-Closeout Checklist", 3,
            (
                "inventory every cleanup target and resolve its ownership to the completed PR before deletion",
                "completed implementation and verification worktrees",
                "PR-owned Docker containers, images, volumes, and networks",
                "PR-owned temporary clones, files, and isolated dependencies",
                "do not run broad prune operations",
                "hash staged, unstaged, and untracked state before and after preservation",
                "verify `main...origin/main` is `0` ahead and `0` behind",
                "retained, deleted, and recoverability",
                "prove scoped resources are absent",
            ),
        ),
    )
    failures = cleanup_authority_anchor_failures(
        lambda path: read_document(path).encode("utf-8")
    )
    for path, heading, level, markers in specifications:
        try:
            document = read_document(path)
            body = markdown_heading_body(document, heading, level)
        except (OSError, UnicodeError) as error:
            failures.append(f"Stage 8 merge-closeout contract unavailable: {path}: {error}.")
            continue
        normalized = re.sub(r"\s+", " ", body)
        failures.extend(
            f"Stage 8 merge-closeout contract missing {path} marker: {marker}."
            for marker in markers if marker not in normalized
        )
        if has_unsafe_broad_prune_authorization(document):
            failures.append(
                f"Stage 8 merge-closeout contract contains unsafe broad-prune authorization: {path}."
            )
    return failures


def security_preflight_failures(root: Path, issue: int) -> list[str]:
    path = root / f"docs/governance/preflights/issue-{issue}.json"
    schema, expected_sha = SECURITY_PREFLIGHTS[issue]
    try:
        metadata = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 65536:
            raise ValueError("preflight must be a bounded regular file")
        payload = path.read_bytes()
        artifact = load_json_without_duplicate_members(path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateJsonMember, ValueError):
        return [f"Issue #{issue} security preflight is malformed or unreadable."]
    failures: list[str] = []
    if hashlib.sha256(payload).hexdigest() != expected_sha:
        failures.append(f"Issue #{issue} security preflight exact bytes drifted.")
    if artifact.get("schema_version") != schema:
        failures.append(f"Issue #{issue} security preflight schema drifted.")
    expected_branch = {
        150: ISSUE150_BRANCH,
        428: ISSUE428_BRANCH,
        460: ISSUE460_BRANCH,
    }[issue]
    if artifact.get("issue_number") != issue or artifact.get("branch") != expected_branch:
        failures.append(f"Issue #{issue} security preflight identity drifted.")
    scope = artifact.get("scope")
    required = scope.get("required") if isinstance(scope, dict) else None
    forbidden = scope.get("forbidden") if isinstance(scope, dict) else None
    expected = set(ROUTES[expected_branch])
    if issue == 460:
        expected -= ISSUE460_CORRECTION_PATHS | ISSUE460_HOSTED_SECURITY_PATHS
    if not isinstance(required, list) or set(required) != expected or len(required) != len(expected):
        failures.append(f"Issue #{issue} security preflight scope drifted.")
    if not isinstance(forbidden, list) or any(
        path == rule or (isinstance(rule, str) and rule.endswith("/") and path.startswith(rule))
        for path in expected for rule in (forbidden if isinstance(forbidden, list) else [])
    ):
        failures.append(f"Issue #{issue} security preflight forbidden scope conflicts.")
    return failures


def issue424_governance_failures(root: Path) -> list[str]:
    """Validate the exact controller proposal without network or mutable external state."""
    failures: list[str] = []
    controller_path = root / "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md"
    binding_path = root / "docs/governance/narratwin-master-program-v1.json"
    preflight_path = root / "docs/governance/preflights/issue-424.json"
    try:
        controller_bytes = controller_path.read_bytes()
        controller = controller_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return ["Issue #424 controller bytes are unavailable or invalid UTF-8."]
    headings = tuple(re.findall(r"^## ([0-9]+\. .+)$", controller, flags=re.MULTILINE))
    if headings != ISSUE424_HEADINGS:
        failures.append("Issue #424 numbered heading order/titles differ from the exact 42-section contract.")
    if "exact waist-up derivative path and SHA-256" not in controller:
        failures.append("Issue #424 controller omits the exact waist-up derivative path and SHA-256 invariant.")
    actual_fingerprint = (
        hashlib.sha256(controller_bytes).hexdigest(),
        len(controller_bytes),
        len(controller_bytes.splitlines()),
        controller_bytes.endswith(b"\n"),
    )
    expected_fingerprint = (
        ISSUE424_CONTROLLER_SHA256,
        ISSUE424_CONTROLLER_BYTES,
        ISSUE424_CONTROLLER_LINES,
        ISSUE424_CONTROLLER_HAS_TRAILING_NEWLINE,
    )
    if actual_fingerprint != expected_fingerprint:
        failures.append("Issue #424 pinned controller fingerprint is inconsistent.")

    try:
        binding = load_json_without_duplicate_members(binding_path)
    except DuplicateJsonMember:
        return failures + ["Issue #424 proposal binding contains a duplicate JSON member."]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return failures + ["Issue #424 proposal binding is unavailable or invalid JSON."]
    if not isinstance(binding, dict):
        return failures + ["Issue #424 proposal binding must be a JSON object."]
    unknown = sorted(set(binding) - ISSUE424_BINDING_FIELDS)
    missing = sorted(ISSUE424_BINDING_FIELDS - set(binding))
    if unknown:
        failures.append(f"Issue #424 unknown binding field: {unknown[0]}")
    if missing:
        failures.append(f"Issue #424 missing binding field: {missing[0]}")
    expected_scalars = {
        "schemaVersion": "MasterProgramProposalBindingV1",
        "controllerId": "narratwin-authoritative-master-program-v1",
        "controllerIssue": 424,
        "bootstrapBranch": ISSUE424_BRANCH,
        "acceptedBaseSha": ISSUE424_BASE,
        "documentPath": "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md",
        "documentSha256": ISSUE424_CONTROLLER_SHA256,
        "documentBytes": ISSUE424_CONTROLLER_BYTES,
        "documentLines": ISSUE424_CONTROLLER_LINES,
        "hasTrailingNewline": ISSUE424_CONTROLLER_HAS_TRAILING_NEWLINE,
        "numberedSections": len(ISSUE424_HEADINGS),
        "firstNumberedSection": ISSUE424_HEADINGS[0],
        "lastNumberedSection": ISSUE424_HEADINGS[-1],
        "proposalState": "PROPOSED",
        "implementationAuthority": "NONE",
        "activeProgramRoute": None,
    }
    labels = {
        "documentSha256": "SHA-256", "documentBytes": "byte count",
        "documentLines": "line count", "hasTrailingNewline": "trailing-newline state",
        "acceptedBaseSha": "accepted base", "bootstrapBranch": "branch",
        "proposalState": "proposal state", "implementationAuthority": "implementation authority",
        "activeProgramRoute": "active route",
    }
    for field, expected in expected_scalars.items():
        if binding.get(field) != expected:
            failures.append(f"Issue #424 binding {labels.get(field, field)} is inconsistent.")
    if binding.get("requiredReviews") != ISSUE424_REVIEWS:
        failures.append("Issue #424 binding review contract is inconsistent.")
    if binding.get("requiredApprovals") != ISSUE424_APPROVALS:
        failures.append("Issue #424 binding approval contract is inconsistent.")
    if binding.get("authorityTransition") != ISSUE424_TRANSITION:
        failures.append("Issue #424 separate authority decision transition is inconsistent.")
    if binding.get("predecessor") != ISSUE424_PREDECESSOR:
        failures.append("Issue #424 binding predecessor evidence is inconsistent.")
    if binding.get("prohibitedClaims") != ISSUE424_PROHIBITED_CLAIMS:
        failures.append("Issue #424 binding prohibited-claim contract is inconsistent.")
    if binding.get("routeActivationGuard") != ISSUE424_ROUTE_GUARD:
        failures.append("Issue #424 binding route-activation guard is inconsistent.")
    decision_path = str(ISSUE424_TRANSITION["decisionPath"])
    if decision_path == binding.get("documentPath") or (root / decision_path).exists():
        failures.append("Issue #424 separate authority decision record must not be this proposal or exist in this PR.")

    try:
        preflight = load_json_without_duplicate_members(preflight_path)
    except DuplicateJsonMember:
        failures.append("Issue #424 preflight contains a duplicate JSON member.")
        preflight = None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        preflight = None
    findings = validate_governance_preflight(
        preflight,
        context={"issue_number": 424, "branch": ISSUE424_BRANCH,
                 "changed_files": sorted(ROUTES[ISSUE424_BRANCH])},
    )
    if findings:
        codes = ", ".join(finding.code for finding in findings)
        failures.append(f"Issue #424 GovernancePreflightV1 failed closed: {codes}")
    return failures


def parse_paths_z(output: str) -> list[str]:
    if not output:
        return []
    if not output.endswith("\0"):
        raise RuntimeError("Malformed NUL-delimited Git path output.")
    paths = output[:-1].split("\0")
    if any(not path for path in paths):
        raise RuntimeError("Malformed empty Git path.")
    return paths


def parse_name_status_z(output: str) -> list[str]:
    fields = parse_paths_z(output)
    paths: list[str] = []
    index = 0
    while index < len(fields):
        status_value = fields[index]
        index += 1
        if status_value in {"A", "B", "D", "M", "T", "U"}:
            arity = 1
        elif re.fullmatch(r"[RC]\d{1,3}", status_value) and int(status_value[1:]) <= 100:
            arity = 2
        else:
            raise RuntimeError(f"Malformed Git name-status record: {status_value!r}")
        record_paths = fields[index : index + arity]
        if len(record_paths) != arity:
            raise RuntimeError(f"Incomplete Git name-status record: {status_value!r}")
        paths.extend(record_paths)
        index += arity
    return paths


def route_has_copy_or_rename(output: str) -> bool:
    fields = parse_paths_z(output)
    found = False
    index = 0
    while index < len(fields):
        status_value = fields[index]
        index += 1
        if status_value in {"A", "B", "M", "T", "U"}:
            arity = 1
        elif status_value == "D":
            arity, found = 1, True
        elif re.fullmatch(r"[RC]\d{1,3}", status_value) and int(status_value[1:]) <= 100:
            arity = 2
            found = True
        else:
            raise RuntimeError(f"Malformed Git name-status record: {status_value!r}")
        if len(fields[index:index + arity]) != arity:
            raise RuntimeError(f"Incomplete Git name-status record: {status_value!r}")
        index += arity
    return found


def route_base(run: Callable[[list[str]], Any], branch: str) -> str:
    if branch == ISSUE459_BRANCH:
        commits = (ISSUE459_BASE, ISSUE459_FROZEN_HEAD, ISSUE459_TRANSITION_BASE, ISSUE459_TRANSITION_MERGE)
        resolved = [run(["git", "rev-parse", f"{commit}^{{commit}}"]) for commit in commits]
        edges = ((ISSUE459_BASE, ISSUE459_FROZEN_HEAD), (ISSUE459_FROZEN_HEAD, "HEAD"),
                 (ISSUE459_TRANSITION_BASE, "HEAD"), (ISSUE459_TRANSITION_MERGE, "HEAD"))
        ancestors = [run(["git", "merge-base", "--is-ancestor", *edge]) for edge in edges]
        parents = run(["git", "show", "-s", "--format=%P", ISSUE459_TRANSITION_MERGE])
        expected_parents = f"{ISSUE459_FROZEN_HEAD} {ISSUE459_TRANSITION_BASE}"
        if (any(result.returncode for result in [*resolved, *ancestors, parents]) or
                [str(result.stdout).strip() for result in resolved] != list(commits) or
                str(parents.stdout).strip() != expected_parents):
            raise RuntimeError("Issue #459 reviewed transition evidence is unavailable or inconsistent.")
        return ISSUE459_TRANSITION_BASE
    if branch == ISSUE466_BRANCH:
        commits = (
            ISSUE466_BASE,
            ISSUE466_FROZEN_HEAD,
            ISSUE466_TRANSITION_BASE,
            ISSUE466_TRANSITION_MERGE,
        )
        resolved = [run(["git", "rev-parse", f"{commit}^{{commit}}"]) for commit in commits]
        current = run(["git", "rev-parse", "origin/main^{commit}"])
        edges = (
            (ISSUE466_BASE, ISSUE466_FROZEN_HEAD),
            (ISSUE466_FROZEN_HEAD, "HEAD"),
            (ISSUE466_TRANSITION_BASE, "HEAD"),
            (ISSUE466_TRANSITION_MERGE, "HEAD"),
        )
        ancestors = [run(["git", "merge-base", "--is-ancestor", *edge]) for edge in edges]
        parents = run(["git", "show", "-s", "--format=%P", ISSUE466_TRANSITION_MERGE])
        expected_parents = f"{ISSUE466_FROZEN_HEAD} {ISSUE466_TRANSITION_BASE}"
        if (
            any(result.returncode for result in [*resolved, current, *ancestors, parents])
            or [str(result.stdout).strip() for result in resolved] != list(commits)
            or str(current.stdout).strip() != ISSUE466_TRANSITION_BASE
            or str(parents.stdout).strip() != expected_parents
        ):
            raise RuntimeError(
                "Issue #466 reviewed transition evidence is unavailable or inconsistent."
            )
        return ISSUE466_TRANSITION_BASE
    if branch == ISSUE479_BRANCH:
        commits = (
            ISSUE479_BASE, ISSUE479_FROZEN_HEAD,
            ISSUE479_TRANSITION_BASE, ISSUE479_TRANSITION_MERGE,
        )
        resolved = [run(["git", "rev-parse", f"{commit}^{{commit}}"]) for commit in commits]
        current = run(["git", "rev-parse", "origin/main^{commit}"])
        edges = (
            (ISSUE479_BASE, ISSUE479_FROZEN_HEAD),
            (ISSUE479_FROZEN_HEAD, "HEAD"),
            (ISSUE479_TRANSITION_BASE, "HEAD"),
            (ISSUE479_TRANSITION_MERGE, "HEAD"),
        )
        ancestors = [run(["git", "merge-base", "--is-ancestor", *edge]) for edge in edges]
        parents = run(["git", "show", "-s", "--format=%P", ISSUE479_TRANSITION_MERGE])
        if (
            any(result.returncode for result in [*resolved, current, *ancestors, parents])
            or [str(result.stdout).strip() for result in resolved] != list(commits)
            or str(current.stdout).strip() != ISSUE479_TRANSITION_BASE
            or str(parents.stdout).strip() != f"{ISSUE479_FROZEN_HEAD} {ISSUE479_TRANSITION_BASE}"
        ):
            raise RuntimeError(
                "Issue #479 reviewed transition evidence is unavailable or inconsistent."
            )
        return ISSUE479_TRANSITION_BASE
    if branch == ISSUE494_BRANCH:
        commits = (
            ISSUE494_BASE, ISSUE494_FROZEN_HEAD,
            ISSUE494_TRANSITION_BASE, ISSUE494_TRANSITION_MERGE,
        )
        resolved = [run(["git", "rev-parse", f"{commit}^{{commit}}"])
                    for commit in commits]
        current = run(["git", "rev-parse", "origin/main^{commit}"])
        edges = (
            (ISSUE494_BASE, ISSUE494_FROZEN_HEAD),
            (ISSUE494_FROZEN_HEAD, "HEAD"),
            (ISSUE494_TRANSITION_BASE, "HEAD"),
            (ISSUE494_TRANSITION_MERGE, "HEAD"),
        )
        ancestors = [run(["git", "merge-base", "--is-ancestor", *edge])
                     for edge in edges]
        parents = run(["git", "show", "-s", "--format=%P", ISSUE494_TRANSITION_MERGE])
        if (
            any(result.returncode for result in [*resolved, current, *ancestors, parents])
            or [str(result.stdout).strip() for result in resolved] != list(commits)
            or str(current.stdout).strip() != ISSUE494_TRANSITION_BASE
            or str(parents.stdout).strip()
            != f"{ISSUE494_FROZEN_HEAD} {ISSUE494_TRANSITION_BASE}"
        ):
            raise RuntimeError(
                "Issue #494 reviewed transition evidence is unavailable or inconsistent."
            )
        return ISSUE494_TRANSITION_BASE
    fixed_routes = {
        ISSUE502_BRANCH: (502, ISSUE502_BASE),
        ISSUE499_BRANCH: (499, ISSUE499_BASE),
        ISSUE495_BRANCH: (495, ISSUE495_BASE),
        ISSUE482_BRANCH: (482, ISSUE482_BASE),
        ISSUE478_BRANCH: (478, ISSUE478_BASE),
        ISSUE475_BRANCH: (475, ISSUE475_BASE),
        ISSUE468_BRANCH: (468, ISSUE468_BASE),
        ISSUE473_BRANCH: (473, ISSUE473_BASE),
        ISSUE471_BRANCH: (471, ISSUE471_BASE),
        ISSUE459_T05B_BRANCH: (459, ISSUE459_T05B_BASE),
        ISSUE459_T05A_BRANCH: (459, ISSUE459_T05A_BASE),
        ISSUE459_T03_BRANCH: (459, ISSUE459_T03_BASE),
        ISSUE460_BRANCH: (460, ISSUE460_BASE),
        ISSUE452_BRANCH: (452, ISSUE452_BASE),
        ISSUE451_BRANCH: (451, ISSUE451_BASE),
        ISSUE150_BRANCH: (150, ISSUE150_BASE),
        ISSUE424_BRANCH: (424, ISSUE424_BASE),
        ISSUE421_BRANCH: (421, ISSUE421_BASE),
        ISSUE368_IMPLEMENTATION_BRANCH: (368, ISSUE368_IMPLEMENTATION_BASE),
        ISSUE368_QUOTA_FIX_BRANCH: (368, ISSUE368_QUOTA_FIX_BASE),
        ISSUE368_BINDING_COMPAT_BRANCH: (368, ISSUE368_BINDING_COMPAT_BASE),
        ISSUE368_AUTH_TRANSPORT_BRANCH: (368, ISSUE368_REFRESH_TRANSPORT_BASE),
        ISSUE368_TIMEOUT_BRANCH: (368, ISSUE368_TIMEOUT_BASE),
        ISSUE498_BRANCH: (498, ISSUE498_BASE),
        ISSUE368_PROMPT_BRANCH: (368, ISSUE368_PROMPT_BASE),
        ISSUE368_BRANCH: (368, ISSUE368_BASE),
        ISSUE386_BRANCH: (386, ISSUE386_BASE),
        ISSUE415_CORRECTION_BRANCH: (415, "20c1f4f19ee20e613f87bbfa6339f17ebb0ad205"),
        ISSUE486_BRANCH: (486, ISSUE486_BASE),
        ISSUE486_PROTECTED_BRANCH: (486, ISSUE486_PROTECTED_BASE),
        ISSUE486_HASH_CLEANUP_BRANCH: (486, ISSUE486_HASH_CLEANUP_BASE),
    }
    if branch in fixed_routes:
        issue, base = fixed_routes[branch]
        fixed = run(["git", "rev-parse", f"{base}^{{commit}}"])
        common = run(["git", "merge-base", base, "HEAD"])
        fixed_value = str(fixed.stdout).strip()
        common_value = str(common.stdout).strip()
        fixed_invalid = (
            fixed.returncode or common.returncode
            or fixed_value != base or common_value != base
        )
        branch_point_invalid = False
        if not fixed_invalid and branch in {ISSUE502_BRANCH, ISSUE479_BRANCH, ISSUE482_BRANCH, ISSUE478_BRANCH, ISSUE475_BRANCH, ISSUE468_BRANCH, ISSUE486_BRANCH, ISSUE486_PROTECTED_BRANCH, ISSUE486_HASH_CLEANUP_BRANCH, ISSUE473_BRANCH, ISSUE471_BRANCH, ISSUE459_T05B_BRANCH, ISSUE459_T05A_BRANCH, ISSUE459_T03_BRANCH, ISSUE460_BRANCH, ISSUE452_BRANCH, ISSUE451_BRANCH, ISSUE150_BRANCH, ISSUE424_BRANCH, ISSUE421_BRANCH, ISSUE368_IMPLEMENTATION_BRANCH, ISSUE368_BINDING_COMPAT_BRANCH, ISSUE368_AUTH_TRANSPORT_BRANCH, ISSUE368_TIMEOUT_BRANCH,
                      ISSUE368_QUOTA_FIX_BRANCH, ISSUE498_BRANCH, ISSUE368_BRANCH,
                      ISSUE368_PROMPT_BRANCH}:
            branch_point = run(["git", "merge-base", "origin/main", "HEAD"])
            branch_point_invalid = branch_point.returncode != 0 or str(branch_point.stdout).strip() != base
        if fixed_invalid or branch_point_invalid:
            raise RuntimeError(f"Issue #{issue} fixed base evidence is unavailable or inconsistent.")
        return base
    current = run(["git", "rev-parse", "origin/main^{commit}"])
    common = run(["git", "merge-base", "origin/main", "HEAD"])
    current_value = str(current.stdout).strip()
    common_value = str(common.stdout).strip()
    if current.returncode or common.returncode or not re.fullmatch(r"[0-9a-f]{40}", current_value):
        raise RuntimeError("Cut 1 current main evidence is unavailable.")
    if common_value != current_value:
        raise RuntimeError("Cut 1 route does not descend from current main.")
    return current_value


def route_text_charges(
    run: Callable[[list[str]], Any], base: str, paths: set[str]
) -> tuple[int, dict[str, int]]:
    ordered = sorted(paths)
    untracked = run(["git", "ls-files", "-z", "--others", "--exclude-standard", "--", *ordered])
    if untracked.returncode:
        raise RuntimeError(untracked.stderr.strip() or "Route untracked-text evidence failed.")
    if untracked.stdout:
        found = parse_paths_z(untracked.stdout)
        raise RuntimeError(f"Route required text path is untracked: {found[0]}")
    snapshots: list[dict[str, int]] = []
    for cached in (True, False):
        charges: dict[str, int] = {}
        for path in ordered:
            args = ["git", "diff"] + (["--cached"] if cached else [])
            result = run([*args, "--numstat", "--no-renames", base, "--", path])
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "Route charged-line evidence failed.")
            rows = result.stdout.splitlines()
            if len(rows) > 1:
                raise RuntimeError("Route charged-line evidence contains an unexpected path.")
            if not rows:
                continue
            fields = rows[0].split("\t")
            if len(fields) != 3 or fields[2] != path:
                raise RuntimeError("Route charged-line evidence contains an unexpected path.")
            if not fields[0].isdigit() or not fields[1].isdigit():
                raise RuntimeError("Route charged-line evidence is malformed or binary.")
            charges[path] = int(fields[0]) + int(fields[1])
        snapshots.append(charges)
    all_paths = set().union(*snapshots)
    return max(sum(snapshot.values()) for snapshot in snapshots), {
        path: max(snapshot.get(path, 0) for snapshot in snapshots) for path in all_paths
    }


def cut1_transition_charges(
    run: Callable[[list[str]], Any], base: str, _paths: set[str]
) -> tuple[int, dict[str, int]]:
    merge = run(["git", "merge-base", base, "HEAD"])
    if merge.returncode or merge.stdout.strip() != base:
        raise RuntimeError("Issue #366 base diff unavailable.")
    results = (
        run(["git", "diff", "--cached", "--numstat", base, "--"]),
        run(["git", "diff", "--numstat", base, "--"]),
    )
    if any(result.returncode for result in results):
        raise RuntimeError("Issue #366 base diff unavailable.")
    try:
        charges = [
            {path: int(added) + int(deleted) for added, deleted, path in
             (line.split("\t") for line in result.stdout.splitlines())}
            for result in results
        ]
    except ValueError as error:
        raise RuntimeError("Issue #366 malformed or binary numstat.") from error
    charged_paths = set().union(*charges)
    return max(sum(snapshot.values()) for snapshot in charges), {
        path: max(snapshot.get(path, 0) for snapshot in charges) for path in charged_paths
    }


def route_binary_sizes(root: Path, paths: set[str], encoding: str | None = None) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for path in sorted(paths):
        target = root / path
        try:
            metadata = target.lstat()
        except FileNotFoundError as error:
            raise RuntimeError(f"Route binary is missing: {path}") from error
        if target.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError(f"Route binary must be a regular non-symlink file: {path}")
        if metadata.st_size <= 0:
            raise RuntimeError(f"Route binary is empty: {path}")
        if encoding:
            try:
                target.read_text(encoding=encoding)
            except UnicodeError as error:
                raise RuntimeError(f"Route file is not valid {encoding}: {path}") from error
        sizes[path] = metadata.st_size
    return sizes


def route_text_integrity(root: Path, run: Callable[[list[str]], Any], paths: set[str]) -> None:
    route_binary_sizes(root, paths, "utf-8")
    ordered = sorted(paths)
    commands = (
        (["git", "ls-tree", "-r", "-z", "HEAD", "--", *ordered],
         r"([0-9]{6}) (blob|commit) ([0-9a-f]{40,64})\t(.+)", "HEAD"),
        (["git", "ls-files", "--stage", "-z", "--", *ordered],
         r"([0-9]{6}) ([0-9a-f]{40,64}) ([0-3])\t(.+)", "index"),
    )
    for command, pattern, label in commands:
        result = run(command)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or f"Route text {label}-mode evidence failed.")
        found: set[str] = set()
        for record in parse_paths_z(str(result.stdout)):
            match = re.fullmatch(pattern, record)
            if match is None:
                raise RuntimeError(f"Route text {label}-mode evidence is malformed.")
            groups = match.groups()
            mode, path = groups[0], groups[3]
            kind = groups[1] if label == "HEAD" else groups[2]
            if path not in paths or path in found:
                raise RuntimeError(f"Route text {label}-mode evidence has an unexpected path.")
            if mode != "100644" or kind not in {"blob", "0"}:
                raise RuntimeError(f"Route text must be an ordinary tracked file: {path}")
            found.add(path)
        if found != paths:
            raise RuntimeError(f"Route text {label}-mode evidence is missing: {sorted(paths - found)[0]}")


def issue459_snapshot_failures(root: Path, commit: str, sources: dict[str, str], label: str) -> list[str]:
    try:
        text = (root / "docs/governance/ISSUE_459_CONTROLLED_PRESENTER_PREFLIGHT_V1.md").read_text(encoding="utf-8")
        environment = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_NO_LAZY_FETCH": "1"}
        failures: list[str] = []
        for path, expected in sources.items():
            result = subprocess.run(["/usr/bin/git", "show", f"{commit}:{path}"], cwd=root,
                env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=5)
            if (result.returncode or hashlib.sha256(result.stdout).hexdigest() != expected or
                    f"`{expected}`" not in text):
                failures.append(f"Issue #459 {label} identity drifted: {path}")
        return failures
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as error:
        return [f"Issue #459 {label} freeze failed closed: {error}"]


def issue459_source_failures(root: Path) -> list[str]:
    failures = issue459_snapshot_failures(
        root, ISSUE459_FROZEN_HEAD, ISSUE459_SOURCE_SHA256, "frozen source")
    text = (root / "docs/governance/ISSUE_459_CONTROLLED_PRESENTER_PREFLIGHT_V1.md").read_text(encoding="utf-8")
    failures.extend(f"Issue #459 editable authority identity drifted: {label}"
                    for label, expected in ISSUE459_EDITABLE_AUTHORITY_SHA256.items()
                    if label not in text or f"`{expected}`" not in text)
    return failures


def issue459_base_source_failures(root: Path) -> list[str]:
    return issue459_snapshot_failures(root, ISSUE459_BASE, ISSUE459_BASE_SOURCE_SHA256, "base source")


def issue498_commit_topology_failures(run: Callable[[list[str]], Any]) -> list[str]:
    parents_result = run(["git", "show", "-s", "--format=%P", "HEAD"])
    if parents_result.returncode:
        return ["Issue #498 exact TDD commit topology drifted."]
    parents = str(parents_result.stdout).strip().split()
    if len(parents) == 1 and re.fullmatch(r"[0-9a-f]{40}", parents[0]):
        candidate = "HEAD"
    elif (
        len(parents) == 2
        and parents[0] == ISSUE498_BASE
        and re.fullmatch(r"[0-9a-f]{40}", parents[1])
    ):
        candidate = parents[1]
    else:
        return ["Issue #498 exact TDD commit topology drifted."]
    result = run(
        [
            "git",
            "log",
            "--reverse",
            "-z",
            "--format=%H%x00%s",
            f"{ISSUE498_BASE}..{candidate}",
        ]
    )
    if result.returncode:
        return ["Issue #498 exact TDD commit topology drifted."]
    fields = str(result.stdout).split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    if len(fields) != len(ISSUE498_COMMIT_TOPOLOGY) * 2:
        return ["Issue #498 exact TDD commit topology drifted."]
    actual = list(zip(fields[::2], fields[1::2], strict=True))
    for (commit, subject), (expected_commit, expected_subject) in zip(
        actual, ISSUE498_COMMIT_TOPOLOGY, strict=True
    ):
        if (
            re.fullmatch(r"[0-9a-f]{40}", commit) is None
            or (expected_commit is not None and commit != expected_commit)
            or subject != expected_subject
        ):
            return ["Issue #498 exact TDD commit topology drifted."]
    return []


def check_exact_route(
    root: Path, run: Callable[[list[str]], Any], branch: str, changed: set[str], failures: list[str]
) -> None:
    if branch not in ROUTES:
        collision = next(
            (
                exact
                for exact in sorted(ROUTES, key=len, reverse=True)
                if branch.startswith(f"{exact}-")
            ),
            None,
        )
        if collision is not None:
            failures.append(
                f"Stage 8 branch collides with exact reviewed route {collision}: {branch}."
            )
        return
    issue = ROUTE_ISSUES[branch]
    files = ROUTES[branch]
    effective_changed = set(changed)
    fixed_base: str | None = None
    if branch == ISSUE498_BRANCH:
        failures.extend(issue498_commit_topology_failures(run))
    if branch == ISSUE459_BRANCH:
        try:
            fixed_base = route_base(run, branch)
            snapshots = (
                run([
                    "git", "diff", "--name-only", "-z", "--no-renames",
                    f"{ISSUE459_BASE}..{ISSUE459_FROZEN_HEAD}", "--",
                ]),
                run([
                    "git", "diff", "--name-only", "-z", "--no-renames",
                    f"{ISSUE459_TRANSITION_BASE}..HEAD", "--",
                ]),
            )
            if any(snapshot.returncode for snapshot in snapshots):
                raise RuntimeError("Issue #459 transition route evidence is unavailable.")
            for paths, expected in zip((set(parse_paths_z(str(snapshot.stdout))) | (effective_changed & ISSUE459_HOSTED_CORRECTION_PATHS if index else set()) for index, snapshot in enumerate(snapshots)), (files - ISSUE459_HOSTED_CORRECTION_PATHS, files), strict=True):
                effective_changed.update(paths)
                failures.extend(
                    f"Issue #459 route contains unauthorized path: {path}"
                    for path in sorted(paths - expected)
                )
                failures.extend(f"Issue #459 route snapshot is missing required path: {path}"
                                for path in sorted(expected - paths))
        except RuntimeError as error:
            failures.append(str(error))
    elif branch == ISSUE479_BRANCH:
        try:
            fixed_base = route_base(run, branch)
            snapshots = (
                run(["git", "diff", "--name-only", "-z", "--no-renames",
                     f"{ISSUE479_BASE}..{ISSUE479_FROZEN_HEAD}", "--"]),
                run(["git", "diff", "--name-only", "-z", "--no-renames",
                     f"{ISSUE479_TRANSITION_BASE}..HEAD", "--"]),
            )
            if any(snapshot.returncode for snapshot in snapshots):
                raise RuntimeError("Issue #479 transition route evidence is unavailable.")
            for snapshot in snapshots:
                paths = set(parse_paths_z(str(snapshot.stdout)))
                effective_changed.update(paths)
                failures.extend(f"Issue #479 route contains unauthorized path: {path}"
                                for path in sorted(paths - files))
                failures.extend(f"Issue #479 route snapshot is missing required path: {path}"
                                for path in sorted(files - paths))
        except RuntimeError as error:
            failures.append(str(error))
    elif branch == ISSUE494_BRANCH:
        try:
            fixed_base = route_base(run, branch)
            snapshots = (
                run(["git", "diff", "--name-only", "-z", "--no-renames",
                     f"{ISSUE494_BASE}..{ISSUE494_FROZEN_HEAD}", "--"]),
                run(["git", "diff", "--name-only", "-z", "--no-renames",
                     f"{ISSUE494_TRANSITION_BASE}..HEAD", "--"]),
            )
            if any(snapshot.returncode for snapshot in snapshots):
                raise RuntimeError("Issue #494 transition route evidence is unavailable.")
            for snapshot in snapshots:
                paths = set(parse_paths_z(str(snapshot.stdout)))
                effective_changed.update(paths)
                failures.extend(f"Issue #494 route contains unauthorized path: {path}"
                                for path in sorted(paths - files))
                failures.extend(f"Issue #494 route snapshot is missing required path: {path}"
                                for path in sorted(files - paths))
        except RuntimeError as error:
            failures.append(str(error))
    failures.extend(
        f"Issue #{issue} route is missing required path: {path}"
        for path in sorted(files - effective_changed)
    )
    failures.extend(
        f"Issue #{issue} route changed unexpected path: {path}"
        for path in sorted(effective_changed - files)
    )
    if branch == ISSUE502_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-502.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 502, "branch": branch, "changed_files": sorted(files)},
            )
            failures.extend(
                f"Issue #502 governance preflight failed: {item.code}"
                for item in findings
            )
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            issue502_authority = (
                ISSUE502_BASE,
                ISSUE502_TREE,
                ISSUE502_ROUTE_COMMENT,
                ISSUE502_ROUTE_SHA256,
            )
            if not isinstance(objective, str) or any(
                value not in objective for value in issue502_authority
            ):
                failures.append("Issue #502 security authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #502 governance preflight failed closed: {error}")
    elif branch == ISSUE479_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-479.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 479, "branch": branch, "changed_files": sorted(files)},
            )
            failures.extend(f"Issue #479 governance preflight failed: {item.code}" for item in findings)
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            issue479_authority = (
                ISSUE479_BASE, ISSUE479_ROUTE_COMMENT, ISSUE479_ROUTE_SHA256,
                ISSUE479_CLARIFICATION_COMMENT, ISSUE479_CLARIFICATION_SHA256,
                ISSUE479_BUDGET_COMMENT, ISSUE479_BUDGET_SHA256,
                ISSUE479_FROZEN_HEAD, ISSUE479_TRANSITION_BASE, ISSUE479_TRANSITION_MERGE,
                ISSUE479_TRANSITION_COMMENT, ISSUE479_TRANSITION_SHA256,
            )
            if not isinstance(objective, str) or any(
                value not in objective for value in issue479_authority
            ):
                failures.append("Issue #479 T05C authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #479 governance preflight failed closed: {error}")
    if branch == ISSUE494_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-494-google-tts-failure-diagnostics.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 494, "branch": branch,
                         "changed_files": sorted(files)},
            )
            failures.extend(
                f"Issue #494 governance preflight failed: {item.code}" for item in findings
            )
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            issue494_authority = (
                ISSUE494_BASE, ISSUE494_FROZEN_HEAD, ISSUE494_TRANSITION_BASE,
                ISSUE494_TRANSITION_MERGE, ISSUE494_TRANSITION_COMMENT,
                ISSUE494_TRANSITION_SHA256,
            )
            if not isinstance(objective, str) or any(
                value not in objective for value in issue494_authority
            ):
                failures.append("Issue #494 transition authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #494 governance preflight failed closed: {error}")
    if branch == ISSUE368_BINDING_COMPAT_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-368-provider-binding-compat.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 368, "branch": branch, "changed_files": sorted(files)},
            )
            failures.extend(
                f"Issue #368 binding compatibility preflight failed: {item.code}"
                for item in findings
            )
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            required = (ISSUE368_BINDING_COMPAT_BASE, *ISSUE368_BINDING_COMPAT_AUTHORITY)
            if not isinstance(objective, str) or any(value not in objective for value in required):
                failures.append("Issue #368 binding compatibility authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #368 binding compatibility preflight failed closed: {error}")
    if branch == ISSUE499_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-499-pypdf-6-16-2-security-refresh.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 499, "branch": branch, "changed_files": sorted(files)},
            )
            failures.extend(f"Issue #499 governance preflight failed: {item.code}" for item in findings)
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            authority_expected = (
                ISSUE499_BASE,
                ISSUE499_TREE,
                ISSUE499_ROUTE_COMMENT,
                ISSUE499_ROUTE_SHA256,
            )
            if not isinstance(objective, str) or any(
                item not in objective for item in authority_expected
            ):
                failures.append("Issue #499 dependency authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #499 governance preflight failed closed: {error}")
    elif branch == ISSUE495_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-495-browserslist-security-refresh.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 495, "branch": branch, "changed_files": sorted(files)},
            )
            failures.extend(f"Issue #495 governance preflight failed: {item.code}" for item in findings)
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            issue495_authority = (
                ISSUE495_BASE, ISSUE495_TREE, ISSUE495_ROUTE_COMMENT,
                ISSUE495_CORRECTION_COMMENT, ISSUE495_HOSTED_CORRECTION_COMMENT,
                ISSUE495_GUARDRAIL_CORRECTION_COMMENT, ISSUE495_LOCK_SHA256,
            )
            if not isinstance(objective, str) or any(
                value not in objective for value in issue495_authority
            ):
                failures.append("Issue #495 dependency authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #495 governance preflight failed closed: {error}")
    elif branch == ISSUE482_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-482.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 482, "branch": branch, "changed_files": sorted(files)},
            )
            failures.extend(f"Issue #482 governance preflight failed: {item.code}" for item in findings)
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            issue482_authority = (
                ISSUE482_BASE, ISSUE482_BODY_SHA256, ISSUE482_ROUTE_COMMENT, ISSUE482_ROUTE_SHA256,
                ISSUE482_CORRECTION_COMMENT, ISSUE482_CORRECTION_SHA256,
            )
            if not isinstance(objective, str) or any(
                value not in objective for value in issue482_authority
            ):
                failures.append("Issue #482 dependency authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #482 governance preflight failed closed: {error}")
    elif branch == ISSUE478_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-478.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 478, "branch": branch, "changed_files": sorted(files)},
            )
            failures.extend(f"Issue #478 governance preflight failed: {item.code}" for item in findings)
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            if not isinstance(objective, str) or any(value not in objective for value in (
                ISSUE478_BASE, ISSUE478_ROUTE_COMMENT, ISSUE478_ROUTE_SHA256,
                ISSUE478_BRANCH_COMMENT, ISSUE478_BRANCH_SHA256,
                ISSUE478_REVIEW_COMMENT, ISSUE478_REVIEW_SHA256,
            )):
                failures.append("Issue #478 hosted-parity authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #478 governance preflight failed closed: {error}")
    elif branch == ISSUE473_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-473-cleanup-anchor-consumer.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 473, "branch": branch, "changed_files": sorted(files)},
            )
            failures.extend(f"Issue #473 governance preflight failed: {item.code}" for item in findings)
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            if not isinstance(objective, str) or any(
                value not in objective for value in (ISSUE473_BASE, "5470431030")
            ):
                failures.append("Issue #473 cleanup fixture evidence drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #473 governance preflight failed closed: {error}")
    elif branch == ISSUE471_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-471-cleanup-authority-anchor.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 471, "branch": branch, "changed_files": sorted(files)},
            )
            failures.extend(f"Issue #471 governance preflight failed: {item.code}" for item in findings)
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            if not isinstance(objective, str) or any(value not in objective for value in (
                ISSUE471_BASE, "5469282050", "5469309499", "5469332843", *ISSUE471_AUTHORITY_SHA256
            )):
                failures.append("Issue #471 cleanup authority evidence drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #471 governance preflight failed closed: {error}")
    elif branch == ISSUE150_BRANCH:
        failures.extend(security_preflight_failures(root, 150))
        failures.extend(security_preflight_failures(root, 428))
    elif branch == ISSUE428_BRANCH:
        failures.extend(security_preflight_failures(root, 428))
    elif branch == ISSUE460_BRANCH:
        failures.extend(security_preflight_failures(root, 460))
        try:
            artifact = json.loads((root / "docs/governance/preflights/issue-460.json").read_text(encoding="utf-8"))
            findings = validate_governance_preflight(
                artifact,
                context={
                    "issue_number": 460,
                    "branch": branch,
                    "changed_files": sorted(
                        files - ISSUE460_CORRECTION_PATHS - ISSUE460_HOSTED_SECURITY_PATHS
                    ),
                },
            )
            failures.extend(f"Issue #460 governance preflight failed: {finding.code}" for finding in findings)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            failures.append(f"Issue #460 governance preflight failed closed: {error}")
    elif branch == ISSUE468_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-468-scoped-merge-cleanup.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={
                    "issue_number": 468,
                    "branch": branch,
                    "changed_files": sorted(files),
                },
            )
            failures.extend(
                f"Issue #468 governance preflight failed: {finding.code}"
                for finding in findings
            )
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #468 governance preflight failed closed: {error}")
    elif branch == ISSUE475_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-475.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 475, "branch": branch,
                         "changed_files": sorted(files)},
            )
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            issue475_authority = (
                ISSUE475_BASE,
                ISSUE475_RUNTIME_COMMENT,
                ISSUE475_RUNTIME_SHA256,
                ISSUE475_RECEIPT_COMMENT,
                ISSUE475_RECEIPT_SHA256,
                ISSUE475_FREEZE_COMMENT,
                ISSUE475_FREEZE_SHA256,
                ISSUE475_HOSTED_COMMENT,
                ISSUE475_HOSTED_SHA256,
            )
            failures.extend(
                f"Issue #475 governance preflight failed: {finding.code}"
                for finding in findings
            )
            if not isinstance(objective, str) or any(
                value not in objective for value in issue475_authority
            ):
                failures.append("Issue #475 T05B binding authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #475 governance preflight failed closed: {error}")
    elif branch == ISSUE466_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-466.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 466, "branch": branch, "changed_files": sorted(files)},
            )
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            authority = (
                ISSUE466_BASE,
                ISSUE466_AUTHORITY_REVISION,
                ISSUE466_AUTHORITY_SHA256,
                ISSUE466_SPAN_SHA256,
                ISSUE466_FREEZE_COMMENT,
                ISSUE466_FREEZE_SHA256,
                ISSUE466_CORRECTION_COMMENT,
                ISSUE466_CORRECTION_SHA256,
                ISSUE466_SKILL_LEDGER_COMMENT,
                ISSUE466_SKILL_LEDGER_SHA256,
            )
            failures.extend(
                f"Issue #466 governance preflight failed: {finding.code}"
                for finding in findings
            )
            if not isinstance(objective, str) or any(value not in objective for value in authority):
                failures.append("Issue #466 presenter-source authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #466 governance preflight failed closed: {error}")
    elif branch == ISSUE459_T05B_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-459-t05b.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 459, "branch": branch,
                         "changed_files": sorted(files)},
            )
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            t05b_authority = (
                ISSUE459_T05B_BASE,
                ISSUE459_T05B_AUTHORITY_COMMENT,
                ISSUE459_T05B_AUTHORITY_SHA256,
                ISSUE459_T05B_CORRECTION_COMMENT,
                ISSUE459_T05B_CORRECTION_SHA256,
                ISSUE459_T05B_FINGERPRINT_CORRECTION_COMMENT,
                ISSUE459_T05B_FINGERPRINT_CORRECTION_SHA256,
                ISSUE459_T05B_REVIEW_CORRECTION_COMMENT,
                ISSUE459_T05B_REVIEW_CORRECTION_SHA256,
                ISSUE459_T05B_HOSTED_PROVENANCE_COMMENT,
                ISSUE459_T05B_HOSTED_PROVENANCE_SHA256,
            )
            failures.extend(
                f"Issue #459 T05B governance preflight failed: {finding.code}"
                for finding in findings
            )
            if not isinstance(objective, str) or any(
                value not in objective for value in t05b_authority
            ):
                failures.append("Issue #459 T05B governance authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #459 T05B governance preflight failed closed: {error}")
    elif branch == ISSUE459_T05A_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-459-t05a.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 459, "branch": branch,
                         "changed_files": sorted(files)},
            )
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            t05a_authority = (
                ISSUE459_T05A_BASE,
                ISSUE459_T05A_AUTHORITY_COMMENT,
                ISSUE459_T05A_AUTHORITY_SHA256,
            )
            failures.extend(
                f"Issue #459 T05A governance preflight failed: {finding.code}"
                for finding in findings
            )
            if not isinstance(objective, str) or any(
                value not in objective for value in t05a_authority
            ):
                failures.append("Issue #459 T05A governance authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #459 T05A governance preflight failed closed: {error}")
    elif branch == ISSUE459_T03_BRANCH:
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-459-t03.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 459, "branch": branch,
                         "changed_files": sorted(files)},
            )
            objective = preflight.get("objective") if isinstance(preflight, dict) else None
            t03_authority = (
                ISSUE459_T03_BASE,
                ISSUE459_T03_AUTHORITY_COMMENT,
                ISSUE459_T03_AUTHORITY_SHA256,
                ISSUE459_T03_CORRECTION_COMMENT,
                ISSUE459_T03_CORRECTION_SHA256,
                ISSUE459_T03_DEPENDENCY_COMMENT,
                ISSUE459_T03_DEPENDENCY_SHA256,
                ISSUE459_T03_MYRA_CORRECTION_COMMENT,
                ISSUE459_T03_MYRA_CORRECTION_SHA256,
            )
            failures.extend(
                f"Issue #459 T03 governance preflight failed: {finding.code}"
                for finding in findings
            )
            if not isinstance(objective, str) or any(
                value not in objective for value in t03_authority
            ):
                failures.append("Issue #459 T03 governance authority drifted.")
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #459 T03 governance preflight failed closed: {error}")
    if branch == ISSUE424_BRANCH:
        failures.extend(issue424_governance_failures(root))
    if branch == ISSUE459_BRANCH:
        failures.extend(issue459_source_failures(root))
        failures.extend(issue459_base_source_failures(root))
        try:
            preflight = load_json_without_duplicate_members(
                root / "docs/governance/preflights/issue-459.json"
            )
            findings = validate_governance_preflight(
                preflight,
                context={"issue_number": 459, "branch": branch,
                         "changed_files": sorted(files)},
            )
            failures.extend(
                f"Issue #459 governance preflight failed: {finding.code}"
                for finding in findings
            )
        except (OSError, ValueError, TypeError) as error:
            failures.append(f"Issue #459 governance preflight failed closed: {error}")
    try:
        base = fixed_base if fixed_base is not None else route_base(run, branch)
        if branch in {ISSUE495_BRANCH, ISSUE479_BRANCH, ISSUE482_BRANCH, ISSUE478_BRANCH, ISSUE475_BRANCH, ISSUE459_BRANCH, ISSUE459_T03_BRANCH, ISSUE459_T05A_BRANCH,
                      ISSUE459_T05B_BRANCH, ISSUE466_BRANCH, ISSUE494_BRANCH}:
            transition_base = ISSUE459_TRANSITION_BASE if branch == ISSUE459_BRANCH else base
            transitions = (
                *((run(["git", "diff", "--name-status", "-z", "--find-copies-harder",
                        ISSUE479_BASE, ISSUE479_FROZEN_HEAD, "--"]),) if branch == ISSUE479_BRANCH
                   else (run(["git", "diff", "--name-status", "-z", "--find-copies-harder",
                              ISSUE494_BASE, ISSUE494_FROZEN_HEAD, "--"]),)
                   if branch == ISSUE494_BRANCH
                   else () if branch in {ISSUE495_BRANCH, ISSUE482_BRANCH, ISSUE478_BRANCH, ISSUE475_BRANCH, ISSUE459_T03_BRANCH, ISSUE459_T05A_BRANCH,
                                         ISSUE459_T05B_BRANCH, ISSUE466_BRANCH} else (
                    run(["git", "diff", "--name-status", "-z", "--find-copies-harder",
                         ISSUE459_BASE, ISSUE459_FROZEN_HEAD, "--"]),
                )),
                run(["git", "diff", "--name-status", "-z", "--find-copies-harder",
                     transition_base, "HEAD", "--"]),
                run(["git", "diff", "--cached", "--name-status", "-z",
                     "--find-copies-harder", base, "--"]),
                run(["git", "diff", "--name-status", "-z", "--find-copies-harder",
                     base, "--"]),
            )
            if any(result.returncode for result in transitions):
                raise RuntimeError(f"Issue #{issue} rename/copy evidence is unavailable.")
            if any(route_has_copy_or_rename(str(result.stdout)) for result in transitions):
                failures.append(f"Issue #{issue} route forbids deleted, renamed, or copied paths.")
        total, charges = route_text_charges(run, base, set(TEXT_LIMITS[branch]))
        if total > TOTAL_LIMITS[branch]:
            failures.append(f"Issue #{issue} charge {total} exceeds {TOTAL_LIMITS[branch]}.")
        failures.extend(
            f"Issue #{issue} charge for {path} exceeds {limit}."
            for path, limit in TEXT_LIMITS[branch].items() if charges.get(path, 0) > limit
        )
        if branch == ISSUE482_BRANCH:
            route_text_integrity(root, run, files)
        elif branch == ISSUE459_BRANCH:
            sizes = route_binary_sizes(root, files, "utf-8")
            failures.extend(
                f"Issue #459 file {path} must be smaller than {limit} bytes."
                for path, limit in ISSUE459_BYTE_LIMITS.items() if sizes[path] >= limit
            )
        elif branch == ISSUE459_T03_BRANCH:
            sizes = route_binary_sizes(root, set(ISSUE459_T03_BYTE_LIMITS))
            failures.extend(
                f"Issue #459 file {path} must be smaller than {limit} bytes."
                for path, limit in ISSUE459_T03_BYTE_LIMITS.items() if sizes[path] >= limit
            )
        elif branch == ISSUE452_BRANCH:
            sizes = route_binary_sizes(root, set(ISSUE452_BYTE_LIMITS))
            failures.extend(
                f"Issue #452 file {path} must be smaller than {limit} bytes."
                for path, limit in ISSUE452_BYTE_LIMITS.items() if sizes[path] >= limit
            )
        elif branch == ISSUE383_BRANCH:
            sizes = route_binary_sizes(root, ISSUE383_BINARY_FILES)
            failures.extend(
                f"Issue #383 binary {path} exceeds 500000 bytes."
                for path, size in sizes.items() if size > 500000
            )
    except RuntimeError as error:
        failures.append(f"Issue #{issue} route evidence failed closed: {error}")
