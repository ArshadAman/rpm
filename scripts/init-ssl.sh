#!/bin/sh
set -e

DOMAIN="${DOMAIN:-dev.strattonhealth.com}"
EMAIL="${CERTBOT_EMAIL:-admin@${DOMAIN}}"
CERT_NAME="${CERTBOT_CERT_NAME:-$DOMAIN}"
CERT_PATH="/etc/letsencrypt/live/${CERT_NAME}"
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

# ── 2. Check if a valid REAL cert already exists ────────────────────────────
if [ -f "$CERT_PATH/fullchain.pem" ]; then
  ISSUER=$(openssl x509 -noout -issuer -in "$CERT_PATH/fullchain.pem" 2>/dev/null || echo "")
  if echo "$ISSUER" | grep -qi "Let's Encrypt"; then
    # Also check it's not expiring in less than 30 days
    if openssl x509 -checkend 2592000 -noout -in "$CERT_PATH/fullchain.pem" 2>/dev/null; then
      echo "==> [init-ssl] Valid Let's Encrypt cert already exists (not expiring soon). Skipping."
      exit 0
    fi
    echo "==> [init-ssl] Cert expiring soon. Will renew."
  else
    echo "==> [init-ssl] Found dummy/self-signed cert. Removing before requesting real cert..."
    # Remove the dummy cert so certbot can create fresh
    rm -rf "$CERT_PATH"
    # Also clean up any stale renewal config for this cert
    rm -f "/etc/letsencrypt/renewal/${CERT_NAME}.conf"
  fi
fi

# ── 3. Create dummy self-signed cert so nginx can start right away ──────────
# Nginx depends on init-ssl completing, so we can place real cert directly.
# We still create it to ensure the path exists for the nginx template.
echo "==> [init-ssl] Creating temporary self-signed cert for $DOMAIN..."
mkdir -p "$CERT_PATH"
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
  -keyout "$CERT_PATH/privkey.pem" \
  -out "$CERT_PATH/fullchain.pem" \
  -subj "/CN=$DOMAIN" 2>/dev/null

# ── 4. Start a temporary HTTP-only nginx to serve ACME challenge ────────────
mkdir -p "$WEBROOT"
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

# ── 5. Remove dummy cert again so certbot can write the real one ────────────
rm -rf "$CERT_PATH"
rm -f "/etc/letsencrypt/renewal/${CERT_NAME}.conf"

# ── 6. Run certbot ──────────────────────────────────────────────────────────
echo "==> [init-ssl] Requesting Let's Encrypt certificate..."
certbot certonly \
  --webroot \
  --webroot-path="$WEBROOT" \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  --cert-name "$CERT_NAME"

echo "==> [init-ssl] Certificate obtained successfully!"

# ── 7. Stop temp nginx ──────────────────────────────────────────────────────
nginx -c /tmp/acme-nginx.conf -s stop 2>/dev/null || true
echo "==> [init-ssl] Done. Real nginx will now start."
