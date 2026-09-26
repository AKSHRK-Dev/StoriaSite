#!/bin/sh
# Builds the site and uploads it to the web server.
#   HOST=dote@192.168.3.8 ./deploy/deploy.sh
# Needs ssh access; the remote user needs sudo for the first install (nginx config).
set -e
cd "$(dirname "$0")/.."
HOST="${HOST:-dote@192.168.3.8}"
python3 build.py
rsync -az --delete dist/ "$HOST:storia-site/"
scp -q deploy/nginx.conf "$HOST:storia-site.nginx.conf"
ssh -t "$HOST" 'sudo sh -c "
  mkdir -p /var/www/storia &&
  rsync -a --delete ~'"${HOST%%@*}"'/storia-site/ /var/www/storia/ &&
  cp ~'"${HOST%%@*}"'/storia-site.nginx.conf /etc/nginx/sites-available/storia &&
  ln -sf /etc/nginx/sites-available/storia /etc/nginx/sites-enabled/storia &&
  rm -f /etc/nginx/sites-enabled/default &&
  nginx -t && systemctl reload nginx"'
echo "Deployed to $HOST"
