FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DJANGO_SECRET_KEY=build-only-not-used
ENV DJANGO_DEBUG=False
ENV DJANGO_ALLOWED_HOSTS=localhost
ENV DATABASE_URL=sqlite:///db.sqlite3

RUN python manage.py collectstatic --noinput

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

EXPOSE 8000

CMD ["gunicorn", "imso_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
