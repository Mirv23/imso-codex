.PHONY: dev migrate test collectstatic shell

dev:
	python manage.py runserver

migrate:
	python manage.py migrate

test:
	pip install pytest pytest-django && pytest

collectstatic:
	python manage.py collectstatic --noinput

shell:
	python manage.py shell

superuser:
	python manage.py createsuperuser

docker-build:
	docker compose build

docker-up:
	docker compose up

deploy:
	vercel --prod
