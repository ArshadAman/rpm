#!/bin/sh

# Run migrations and setup tasks first
echo "Running migrations..."
python manage.py migrate gigs
python manage.py populate_gig_categories

# Replace the shell process with the actual application process
# Utilizing Gunicorn as a process manager with 2 Uvicorn async workers.
# This keeps the memory footprint low (~250-400MB) while multiplexing connections.
echo "Starting Gunicorn + Uvicorn..."
exec gunicorn rpm.asgi:application -k uvicorn.workers.UvicornWorker -w 2 --bind 0.0.0.0:8000
