#!/bin/bash

set -eo pipefail
shopt -s nullglob

# Database setup
if [ -z ${DB_URL+x} ]; then
  echo "DB_URL needs to be defined!"
  exit
fi

echo "Upgrading the database..."
cd /api
alembic upgrade head

cd -
if [ "$1" = "create_admin" ]; then
  echo "Creating an admin user..."
  python /api/create_admin.py
else
  echo "Starting the API..."
  exec "$@"
fi
