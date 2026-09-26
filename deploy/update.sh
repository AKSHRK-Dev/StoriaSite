#!/bin/sh
# Runs on the web server (cron): pulls the site source, rebuilds with the latest GitHub releases and publishes it.
set -e
cd "$(dirname "$0")/.."
git pull -q --ff-only
python3 build.py > /dev/null
rsync -a --delete dist/ /var/www/storia/
