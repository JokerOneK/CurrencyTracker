#!/bin/sh

until cd /app/backend
do
    echo "Waiting for server volume..."
done

# run a worker and a beat:)
#celery -A backend worker --loglevel=info --concurrency 1 -E
celery -A backend worker --beat --loglevel=info