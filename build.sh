#!/usr/bin/env bash
# build.sh — Render runs this script during every deployment.
# It must be placed at the root of the repository.

set -o errexit   # Exit immediately if any command fails

# Install Python dependencies
pip install -r requirements.txt

# Collect static files into STATIC_ROOT (served by WhiteNoise)
cd food_management
python manage.py collectstatic --no-input

# Apply any pending database migrations
python manage.py migrate
