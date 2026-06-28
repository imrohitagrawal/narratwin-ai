PY ?= $(shell command -v python3 >/dev/null 2>&1 && echo python3 || echo python)

.PHONY: help quality \
	stage0-quality stage1-quality stage2-quality stage3-quality \
	stage4-quality stage5-quality stage6-quality stage7-quality \
	stage8-quality final-review-quality \
	diff-check docs-check backend-lint backend-test frontend-build dependency-security

help:
	@echo "Available targets:"
	@echo "  make quality               Run gates through .stage/current"
	@echo "  make stage0-quality        Validate Stage 0 operating docs and quality setup"
	@echo "  make stage1-quality        Validate Stage 1 product/PRD gate once active"
	@echo "  make stage2-quality        Validate Stage 2 architecture/security gate once active"
	@echo "  make stage3-quality        Validate Stage 3 repo/CI gate once active"
	@echo "  make stage4-quality        Validate Stage 4 first vertical slice once active"
	@echo "  make stage5-quality        Validate Stage 5 eval/guardrail/observability gate once active"
	@echo "  make stage6-quality        Validate Stage 6 multilingual/voice/subtitle gate once active"
	@echo "  make stage7-quality        Validate Stage 7 avatar/export gate once active"
	@echo "  make stage8-quality        Validate Stage 8 release-readiness gate once active"
	@echo "  make final-review-quality  Validate final independent review gate once active"

quality:
	@$(PY) scripts/quality/check_quality_stage.py

stage0-quality: diff-check
	@$(PY) scripts/quality/check_stage0_docs.py

stage1-quality:
	@$(PY) scripts/quality/stage_not_implemented.py 1

stage2-quality:
	@$(PY) scripts/quality/stage_not_implemented.py 2

stage3-quality:
	@$(PY) scripts/quality/stage_not_implemented.py 3

stage4-quality:
	@$(PY) scripts/quality/stage_not_implemented.py 4

stage5-quality:
	@$(PY) scripts/quality/stage_not_implemented.py 5

stage6-quality:
	@$(PY) scripts/quality/stage_not_implemented.py 6

stage7-quality:
	@$(PY) scripts/quality/stage_not_implemented.py 7

stage8-quality:
	@$(PY) scripts/quality/stage_not_implemented.py 8

final-review-quality:
	@$(PY) scripts/quality/stage_not_implemented.py final

# Lightweight checks that work while the repo is still documentation-first.
diff-check:
	@git diff --check

docs-check:
	@echo "Docs are validated by stage-specific quality scripts and GitHub Actions."

# These delegate to CI wrapper scripts once implementation code exists.
backend-lint:
	@if [ -x "./scripts/ci/backend-lint.sh" ]; then ./scripts/ci/backend-lint.sh; else echo "backend lint not applicable yet"; fi

backend-test:
	@if [ -x "./scripts/ci/backend-test.sh" ]; then ./scripts/ci/backend-test.sh; else echo "backend tests not applicable yet"; fi

frontend-build:
	@if [ -x "./scripts/ci/frontend-build.sh" ]; then ./scripts/ci/frontend-build.sh; else echo "frontend build not applicable yet"; fi

dependency-security:
	@if [ -x "./scripts/ci/dependency-security.sh" ]; then ./scripts/ci/dependency-security.sh; else echo "dependency security not applicable yet"; fi
