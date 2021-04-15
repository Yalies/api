#!/usr/bin/env bash

celery -A app.celery worker --loglevel=INFO
