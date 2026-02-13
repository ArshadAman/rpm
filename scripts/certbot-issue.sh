#!/usr/bin/env sh
set -eu

# Load local env file when present.
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

# Optional override for one-off runs.
if [ -n "${CERTBOT_DOMAIN:-}" ]; then
  DOMAIN="$CERTBOT_DOMAIN"
else
  case "${DEPLOY_ENV:-dev}" in
    prod|production)
      DOMAIN="strattonhealth.com"
      ;;
    *)
      DOMAIN="dev.strattonhealth.com"
      ;;
  esac
fi

CERT_NAME="${CERTBOT_CERT_NAME:-rpm-active}"
EMAIL="${CERTBOT_EMAIL:-admin@${DOMAIN}}"

echo "Issuing/refreshing certificate"
echo "DEPLOY_ENV=${DEPLOY_ENV:-dev}"
echo "DOMAIN=${DOMAIN}"
echo "CERT_NAME=${CERT_NAME}"

docker compose run --rm --entrypoint "" certbot \
  certonly \
  --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  --keep-until-expiring \
  --cert-name "$CERT_NAME"

echo "Reloading nginx"
docker compose exec nginx nginx -s reload
