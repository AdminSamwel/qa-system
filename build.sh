#!/usr/bin/env bash
# Render.com build script
set -e

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Running database migrations ==="
flask db upgrade

echo "=== Seeding initial data ==="
flask seed-db

echo "=== Seeding form templates ==="
flask seed-templates

echo "=== Build complete ==="
