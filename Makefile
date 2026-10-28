.PHONY: test check

KIT := $(CURDIR)/plugins/provenote

test:
	python3 -m unittest discover -s tests

check: test
	@if command -v claude >/dev/null 2>&1; then \
	  claude plugin validate --strict plugins/provenote; \
	else echo "skip: claude CLI not found"; fi
	python3 scripts/lint-skills.py
	cd examples/basic && $(KIT)/bin/verify-quotes --strict 01_notes/lit/*.md
	bash scripts/leak-check.sh --tree
