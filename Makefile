.PHONY: quality stage0-quality stage1-quality stage2-quality stage3-quality stage4-quality stage5-quality stage6-quality stage7-quality stage8-quality final-review-quality backend-lint backend-test frontend-build frontend-smoke security docker-build eval-smoke

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

eval-smoke:
	bash scripts/ci/eval-smoke.sh

stage4-quality:
	python3 scripts/quality/check_recommended_review_items.py 4
	python3 scripts/quality/check_stage4_docs.py
	bash scripts/ci/backend-lint.sh
	bash scripts/ci/backend-test.sh
	bash scripts/ci/frontend-build.sh
	bash scripts/ci/frontend-smoke.sh
	bash scripts/ci/dependency-security.sh
	bash scripts/ci/eval-smoke.sh

stage5-quality:
	python3 scripts/quality/check_recommended_review_items.py 5
	python3 scripts/quality/stage_not_implemented.py "Stage 5"

stage6-quality:
	python3 scripts/quality/check_recommended_review_items.py 6
	python3 scripts/quality/stage_not_implemented.py "Stage 6"

stage7-quality:
	python3 scripts/quality/check_recommended_review_items.py 7
	python3 scripts/quality/stage_not_implemented.py "Stage 7"

stage8-quality:
	python3 scripts/quality/check_recommended_review_items.py 8
	python3 scripts/quality/stage_not_implemented.py "Stage 8"

final-review-quality:
	python3 scripts/quality/check_recommended_review_items.py "Final Review"
	python3 scripts/quality/stage_not_implemented.py "Final Review"
