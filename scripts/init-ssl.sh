#!/bin/sh
set -e

DOMAIN="${DOMAIN:-dev.strattonhealth.com}"
EMAIL="${CERTBOT_EMAIL:-admin@${DOMAIN}}"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}"
OPTIONS_SSL="/etc/letsencrypt/options-ssl-nginx.conf"
DHPARAMS="/etc/letsencrypt/ssl-dhparams.pem"
WEBROOT="/var/www/certbot"

echo "==> [init-ssl] Starting SSL initialization for: $DOMAIN"

# ── 1. Download standard Let's Encrypt helper files if missing ──────────────
if [ ! -f "$OPTIONS_SSL" ]; then
  echo "==> [init-ssl] Downloading options-ssl-nginx.conf..."
  mkdir -p /etc/letsencrypt
  wget -q -O "$OPTIONS_SSL" \
    https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf
fi

if [ ! -f "$DHPARAMS" ]; then
  echo "==> [init-ssl] Downloading ssl-dhparams.pem..."
  wget -q -O "$DHPARAMS" \
    https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem
fi

# ── 2. If real cert already exists and is valid, skip everything ────────────
if [ -f "$CERT_PATH/fullchain.pem" ]; then
  ISSUER=$(openssl x509 -noout -issuer -in "$CERT_PATH/fullchain.pem" 2>/dev/null || echo "")
  if echo "$ISSUER" | grep -qi "Let's Encrypt"; then
    echo "==> [init-ssl] Valid Let's Encrypt cert already exists. Nothing to do."
    exit 0
  fi
  echo "==> [init-ssl] Found dummy/expired cert. Will attempt to replace."
fi

# ── 3. Create dummy self-signed cert so main nginx can always start ─────────
echo "==> [init-ssl] Creating temporary self-signed cert for $DOMAIN..."
mkdir -p "$CERT_PATH"
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
  -keyout "$CERT_PATH/privkey.pem" \
  -out "$CERT_PATH/fullchain.pem" \
  -subj "/CN=$DOMAIN" 2>/dev/null
echo "==> [init-ssl] Temporary cert created."

# ── 4. Start a tiny HTTP-only nginx to serve ACME challenge ────────────────
mkdir -p "$WEBROOT"
# Write a minimal nginx config inline
cat > /tmp/acme-nginx.conf << EOF
events {}
http {
  server {
    listen 80;
    server_name $DOMAIN;
    location /.well-known/acme-challenge/ {
      root $WEBROOT;
    }
    location / {
      return 200 'Obtaining SSL certificate...';
      add_header Content-Type text/plain;
    }
  }
}
EOF

echo "==> [init-ssl] Starting temporary HTTP nginx on port 80..."
nginx -c /tmp/acme-nginx.conf -g "daemon on;"

# ── 5. Run certbot ──────────────────────────────────────────────────────────
echo "==> [init-ssl] Requesting Let's Encrypt certificate..."
certbot certonly \
  --webroot \
  --webroot-path="$WEBROOT" \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  --keep-until-expiring \
  --cert-name "${CERTBOT_CERT_NAME:-rpm-active}"

echo "==> [init-ssl] Certificate obtained successfully!"

# ── 6. Stop temporary nginx, let docker-compose start the real one ──────────
nginx -c /tmp/acme-nginx.conf -s stop 2>/dev/null || true
echo "==> [init-ssl] Done. Real nginx will now start with valid certs."
