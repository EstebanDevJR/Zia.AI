#!/bin/sh
set -e

if [ -z "${DOMAIN}" ] || [ -z "${API_DOMAIN}" ]; then
  echo "DOMAIN and API_DOMAIN must be set in .env"
  exit 1
fi

WWW_DOMAIN="${WWW_DOMAIN:-}"

CERT_DOMAIN="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
CERT_API="/etc/letsencrypt/live/${API_DOMAIN}/fullchain.pem"

if [ -f "$CERT_DOMAIN" ] && [ ! -f "$CERT_API" ]; then
  mkdir -p "/etc/letsencrypt/live/${API_DOMAIN}"
  ln -sf "../${DOMAIN}/fullchain.pem" "/etc/letsencrypt/live/${API_DOMAIN}/fullchain.pem"
  ln -sf "../${DOMAIN}/privkey.pem" "/etc/letsencrypt/live/${API_DOMAIN}/privkey.pem"
fi

if [ -f "$CERT_DOMAIN" ] && [ -f "$CERT_API" ]; then
  TEMPLATE="/etc/nginx/templates/nginx.conf.https.template"
else
  TEMPLATE="/etc/nginx/templates/nginx.conf.http.template"
fi

export DOMAIN API_DOMAIN WWW_DOMAIN
envsubst '${DOMAIN} ${API_DOMAIN} ${WWW_DOMAIN}' < "$TEMPLATE" > /etc/nginx/conf.d/default.conf

exec "$@"
