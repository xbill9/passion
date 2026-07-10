# GRIND404 — the LeetCode Subversion Arcade
# `make help` for the menu.

PYTHON ?= python3
VENV   ?= .venv
BIN     = $(VENV)/bin
HOST   ?= 127.0.0.1
PORT   ?= 8000

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ---- Local development --------------------------------------------------

$(VENV): requirements.txt ## Create the virtualenv and install deps
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	@touch $(VENV)

.PHONY: install
install: $(VENV) ## Install/refresh dependencies into .venv

.PHONY: dev
dev: $(VENV) ## Run with autoreload (http://$(HOST):$(PORT))
	$(BIN)/uvicorn app.main:app --reload --host $(HOST) --port $(PORT)

.PHONY: run
run: $(VENV) ## Run without autoreload
	$(BIN)/uvicorn app.main:app --host $(HOST) --port $(PORT)

.PHONY: health
health: ## Curl the /health endpoint (server must be running)
	curl -fsS http://$(HOST):$(PORT)/health && echo

# ---- Docker -------------------------------------------------------------

.PHONY: up
up: ## docker compose up --build (offline satire, no keys)
	docker compose up --build

.PHONY: down
down: ## docker compose down
	docker compose down

.PHONY: docker-build
docker-build: ## Build the standalone image (tag: grind404)
	docker build -t grind404 .

.PHONY: docker-run
docker-run: ## Run the standalone image on $(PORT)
	docker run --rm -p $(PORT):8000 grind404

# ---- Housekeeping -------------------------------------------------------

.PHONY: clean
clean: ## Remove caches and the local leaderboard
	find . -path ./$(VENV) -prune -o -name '__pycache__' -type d -exec rm -rf {} +
	rm -f app/data/leaderboard.json

.PHONY: distclean
distclean: clean ## Also remove the virtualenv
	rm -rf $(VENV)
