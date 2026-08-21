.PHONY: all validate source-data

all: source-data validate

validate:
	python scripts/validate_release.py

source-data:
	python scripts/rebuild_source_data_archives.py
