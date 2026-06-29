.PHONY: quality stage0-quality stage1-quality stage2-quality stage3-quality stage4-quality stage5-quality stage6-quality stage7-quality stage8-quality final-review-quality

quality:
	python3 scripts/quality/check_quality_stage.py

stage0-quality:
	python3 scripts/quality/check_stage0_docs.py

stage1-quality:
	python3 scripts/quality/check_stage1_docs.py

stage2-quality:
	python3 scripts/quality/check_stage2_docs.py

stage3-quality:
	python3 scripts/quality/stage_not_implemented.py "Stage 3"

stage4-quality:
	python3 scripts/quality/stage_not_implemented.py "Stage 4"

stage5-quality:
	python3 scripts/quality/stage_not_implemented.py "Stage 5"

stage6-quality:
	python3 scripts/quality/stage_not_implemented.py "Stage 6"

stage7-quality:
	python3 scripts/quality/stage_not_implemented.py "Stage 7"

stage8-quality:
	python3 scripts/quality/stage_not_implemented.py "Stage 8"

final-review-quality:
	python3 scripts/quality/stage_not_implemented.py "Final Review"
