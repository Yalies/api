web: gunicorn app:app
worker: REMAP_SIGTERM=SIGQUIT celery -A app.celery worker --loglevel=INFO
