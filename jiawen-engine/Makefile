# Video2Pet Makefile
# ===================
# Quick commands for development and usage

.PHONY: install install-dev setup run serve test clean info help

# Default target
help:
	@echo "Video2Pet - 从视频到宠物数字孪生"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install dependencies"
	@echo "  make install-dev  Install with dev dependencies"
	@echo "  make setup        Full setup (install + download models)"
	@echo ""
	@echo "Usage:"
	@echo "  make run VIDEO=path/to/video.mp4              Run pipeline on video"
	@echo "  make run-fast VIDEO=path/to/video.mp4         Run pipeline (fast mode)"
	@echo "  make run-prompt PROMPT='A corgi in a park'    Generate video and process"
	@echo "  make serve                                    Start web UI"
	@echo ""
	@echo "Development:"
	@echo "  make test         Run tests"
	@echo "  make lint         Run linter"
	@echo "  make clean        Clean output files"
	@echo "  make info         Show system info"

# ─── Setup ───────────────────────────────────────────────────────────

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

setup: install
	@echo "Downloading model weights..."
	mkdir -p models/smal
	@echo "Note: SMAL model must be downloaded manually from https://smal.is.tue.mpg.de/"
	@echo "Place smal_CVPR2018.pkl in models/smal/"
	@echo ""
	@echo "Setup complete! Run 'make info' to check your system."

# ─── Usage ───────────────────────────────────────────────────────────

run:
ifndef VIDEO
	$(error VIDEO is required. Usage: make run VIDEO=path/to/video.mp4)
endif
	python -m video2pet.cli run --video $(VIDEO) --pet-type $(or $(PET_TYPE),dog) --breed $(or $(BREED),generic)

run-fast:
ifndef VIDEO
	$(error VIDEO is required. Usage: make run-fast VIDEO=path/to/video.mp4)
endif
	python -m video2pet.cli run --video $(VIDEO) --pet-type $(or $(PET_TYPE),dog) --breed $(or $(BREED),generic) --fast

run-prompt:
ifndef PROMPT
	$(error PROMPT is required. Usage: make run-prompt PROMPT="A corgi in a park")
endif
	python -m video2pet.cli run --prompt "$(PROMPT)" --pet-type $(or $(PET_TYPE),dog) --breed $(or $(BREED),generic)

serve:
	python web/app.py

# ─── Development ─────────────────────────────────────────────────────

test:
	python -m pytest tests/ -v

lint:
	ruff check video2pet/
	black --check video2pet/

format:
	black video2pet/ scripts/ web/
	ruff check --fix video2pet/

clean:
	rm -rf output/
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

info:
	python -m video2pet.cli info
