web: gunicorn app:app
worker: celery -A app.celery worker --loglevel=INFO
