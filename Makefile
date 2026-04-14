PYTHON ?= python3

.PHONY: install run poll test docker-up docker-down

install:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

run:
	. .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

poll:
	. .venv/bin/activate && python -m app.dev_polling

test:
	. .venv/bin/activate && python -m unittest discover -s tests -v

docker-up:
	docker compose up --build

docker-down:
	docker compose down
