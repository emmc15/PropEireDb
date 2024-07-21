
.PHONY: start
start:
	@echo "Starting worker service..."
	cd src && gunicorn wsgi:server --reload

.PHONY: build
build:
	@echo "Building all services..."
	docker compose build

.PHONY: update
update:
	@echo "Updating Poetry"
	poetry update

.PHONY: run-pipeline
run-pipeline:
	@echo "Running pipeline..."
	cd src && python3 cli.py run-pipeline

.PHONY: run-geoencode
run-geoencode:
	@echo "Running geoencode..."
	cd src && python3 cli.py geoencode-missing-addresses
