.PHONY: up down logs test test-backend test-frontend migrate

up:            ## build and start the full stack (UI on :8080)
	@test -f .env || cp .env.example .env
	docker compose up --build -d
	@echo "UI: http://localhost:8080  API docs: http://localhost:8080/docs"

down:
	docker compose down

logs:
	docker compose logs -f api worker

migrate:
	docker compose exec api alembic upgrade head

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest -q

test-frontend:
	cd frontend && npm run typecheck && npm run build
