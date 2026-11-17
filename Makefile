.PHONY: tls up down logs ps build smoke clean

tls:
	bash scripts/generate_tls.sh

up: tls
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

build: tls
	docker compose build

smoke:
	bash scripts/smoke_test.sh

clean:
	docker compose down -v --remove-orphans
