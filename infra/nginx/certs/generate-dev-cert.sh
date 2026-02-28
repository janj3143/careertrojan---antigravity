#!/usr/bin/env bash
# =============================================================================
# Generate self-signed TLS certificate for local development
# =============================================================================
# Usage:  bash infra/nginx/certs/generate-dev-cert.sh
#         (or run from project root)
#
# Output: infra/nginx/certs/dev.crt  +  infra/nginx/certs/dev.key
# =============================================================================
set -euo pipefail

CERT_DIR="$(cd "$(dirname "$0")" && pwd)"
DAYS=365
DOMAIN="localhost"
SUBJECT="/C=GB/ST=London/L=London/O=CareerTrojan-Dev/CN=${DOMAIN}"

echo "Generating self-signed certificate for ${DOMAIN} ..."
openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "${CERT_DIR}/dev.key" \
    -out    "${CERT_DIR}/dev.crt" \
    -days   ${DAYS} \
    -subj   "${SUBJECT}" \
    -addext "subjectAltName=DNS:${DOMAIN},DNS:*.localhost,IP:127.0.0.1"

chmod 600 "${CERT_DIR}/dev.key"
chmod 644 "${CERT_DIR}/dev.crt"

echo "✅  Certificate generated:"
echo "    ${CERT_DIR}/dev.crt"
echo "    ${CERT_DIR}/dev.key"
echo "    Valid for ${DAYS} days"
