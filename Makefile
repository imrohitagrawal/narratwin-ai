.PHONY: quality docs-check diff-check backend-lint backend-test frontend-build dependency-security

quality: diff-check docs-check backend-lint backend-test frontend-build dependency-security

# Lightweight checks that work while the repo is still documentation-first.
diff-check:
	git diff --check

docs-check:
	@echo "Docs are validated by .github/workflows/quality.yml markdown job in CI."

# These delegate to CI wrapper scripts once implementation code exists.
backend-lint:
	@if [ -x "./scripts/ci/backend-lint.sh" ]; then ./scripts/ci/backend-lint.sh; else echo "backend lint not applicable yet"; fi

backend-test:
	@if [ -x "./scripts/ci/backend-test.sh" ]; then ./scripts/ci/backend-test.sh; else echo "backend tests not applicable yet"; fi

frontend-build:
	@if [ -x "./scripts/ci/frontend-build.sh" ]; then ./scripts/ci/frontend-build.sh; else echo "frontend build not applicable yet"; fi

dependency-security:
	@if [ -x "./scripts/ci/dependency-security.sh" ]; then ./scripts/ci/dependency-security.sh; else echo "dependency security not applicable yet"; fi
