#!/bin/sh
set -e

SOCKFILE=/tmp/gunicorn.sock

# Ensure /tmp exists
mkdir -p /tmp

# Remove directory if it exists
if [ -d "$SOCKFILE" ]; then
  rm -rf "$SOCKFILE"
fi

# Remove socket file if it exists
if [ -S "$SOCKFILE" ]; then
  rm -f "$SOCKFILE"
fi

#echo "Starting Gunicorn..."
#exec gunicorn -k uvicorn.workers.UvicornWorker \
#    --bind unix:$SOCKFILE \
#    --workers 4 \
#    --timeout 120 \
#    main:app

echo "Starting Gunicorn..."
exec gunicorn main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:3000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile '-' \
    --error-logfile '-'