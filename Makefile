.PHONY: quality stage0-quality stage1-quality stage2-quality stage3-quality stage4-quality stage5-quality stage6-quality stage7-quality stage8-quality final-review-quality phase1-closure-quality checkpoint3-acceptance issue280-output-correctness lint typecheck test api-test ui-test e2e eval security ci secrets-scan security-scan dependency-audit container-scan backend-lint backend-test frontend-build frontend-smoke frontend-lighthouse docker-build docker-image-scan eval-smoke performance-smoke

export UV_CACHE_DIR ?= .uv-cache

quality:
	python3 scripts/quality/check_quality_stage.py

stage0-quality:
	python3 scripts/quality/check_recommended_review_items.py 0
	python3 scripts/quality/check_stage0_docs.py

stage1-quality:
	python3 scripts/quality/check_recommended_review_items.py 1
	python3 scripts/quality/check_stage1_docs.py

stage2-quality:
	python3 scripts/quality/check_recommended_review_items.py 2
	python3 scripts/quality/check_stage2_docs.py

stage3-quality:
	python3 scripts/quality/check_recommended_review_items.py 3
	python3 scripts/quality/check_stage3_docs.py
	bash scripts/ci/backend-lint.sh
	bash scripts/ci/backend-test.sh
	bash scripts/ci/frontend-build.sh
	bash scripts/ci/frontend-smoke.sh
	bash scripts/ci/dependency-security.sh
	bash scripts/ci/eval-smoke.sh
	bash scripts/ci/docker-build.sh

backend-lint:
	bash scripts/ci/backend-lint.sh

backend-test:
	bash scripts/ci/backend-test.sh

frontend-build:
	bash scripts/ci/frontend-build.sh

frontend-smoke:
	bash scripts/ci/frontend-smoke.sh

security:
	bash scripts/ci/dependency-security.sh

docker-build:
	bash scripts/ci/docker-build.sh

docker-image-scan:
	bash scripts/ci/docker-image-scan.sh

eval-smoke:
	bash scripts/ci/eval-smoke.sh

frontend-lighthouse:
	bash scripts/ci/frontend-lighthouse.sh

performance-smoke:
	bash scripts/ci/performance-smoke.sh

stage4-quality:
	python3 scripts/quality/check_recommended_review_items.py 4
	python3 scripts/quality/check_stage4_docs.py
	bash scripts/ci/backend-lint.sh
	bash scripts/ci/backend-test.sh
	bash scripts/ci/frontend-build.sh
	bash scripts/ci/frontend-smoke.sh
	bash scripts/ci/dependency-security.sh
	bash scripts/ci/eval-smoke.sh
	bash scripts/ci/docker-build.sh

stage5-quality:
	python3 scripts/quality/check_recommended_review_items.py 5
	python3 scripts/quality/check_stage5_docs.py
	bash scripts/ci/backend-lint.sh
	bash scripts/ci/backend-test.sh
	bash scripts/ci/frontend-build.sh
	bash scripts/ci/frontend-smoke.sh
	bash scripts/ci/dependency-security.sh
	bash scripts/ci/eval-smoke.sh
	bash scripts/ci/docker-build.sh

stage6-quality:
	python3 scripts/quality/check_recommended_review_items.py 6
	python3 scripts/quality/check_stage6_docs.py
	bash scripts/ci/backend-lint.sh
	bash scripts/ci/backend-test.sh
	bash scripts/ci/frontend-build.sh
	bash scripts/ci/frontend-smoke.sh
	bash scripts/ci/dependency-security.sh
	bash scripts/ci/eval-smoke.sh
	bash scripts/ci/docker-build.sh

stage7-quality:
	python3 scripts/quality/check_recommended_review_items.py 7
	python3 scripts/quality/check_stage7_docs.py
	bash scripts/ci/backend-lint.sh
	bash scripts/ci/backend-test.sh
	bash scripts/ci/frontend-build.sh
	bash scripts/ci/frontend-smoke.sh
	bash scripts/ci/dependency-security.sh
	bash scripts/ci/eval-smoke.sh
	bash scripts/ci/docker-build.sh

stage8-quality:
	python3 scripts/quality/check_recommended_review_items.py 8
	python3 scripts/quality/check_stage8_docs.py
	bash scripts/ci/backend-lint.sh
	bash scripts/ci/backend-test.sh
	bash scripts/ci/frontend-build.sh
	bash scripts/ci/frontend-smoke.sh
	bash scripts/ci/performance-smoke.sh
	bash scripts/ci/dependency-security.sh
	bash scripts/ci/eval-smoke.sh
	bash scripts/ci/docker-build.sh
	bash scripts/ci/docker-image-scan.sh
	bash scripts/ci/frontend-lighthouse.sh

final-review-quality:
	python3 scripts/quality/check_recommended_review_items.py "Final Review"
	python3 scripts/quality/check_final_review_docs.py

phase1-closure-quality:
	python3 scripts/quality/check_recommended_review_items.py "Phase 1 Closure"
	python3 scripts/quality/check_phase1_closure_docs.py

checkpoint3-acceptance:
	python3 scripts/quality/check_checkpoint3_acceptance.py

issue280-output-correctness:
	python3 scripts/quality/verify_issue280_output_correctness.py

lint:
	uv run ruff check backend scripts tests
	npm --prefix frontend run lint

typecheck:
	uv run mypy backend scripts tests
	npm --prefix frontend run typecheck

test:
	uv run pytest tests/unit
	npm --prefix frontend test

api-test:
	uv run pytest tests/api

ui-test:
	npm --prefix frontend test

e2e:
	bash scripts/ci/frontend-smoke.sh

eval:
	bash scripts/ci/eval-smoke.sh

ci: quality lint typecheck test api-test ui-test e2e eval security docker-build container-scan frontend-lighthouse

secrets-scan:
	python3 scripts/guardrails_check.py
	bash scripts/ci/dependency-security.sh

security-scan:
	bash scripts/ci/dependency-security.sh

dependency-audit:
	bash scripts/ci/dependency-audit.sh
	npm --prefix frontend audit --audit-level=high

container-scan: docker-build
	bash scripts/ci/docker-image-scan.sh
