#!/usr/bin/env bash
set -euo pipefail
NAMESPACE="${1:-careertrojan}"
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "${NAMESPACE}" create secret generic backend-secrets   --from-literal=DATABASE_URL='postgresql://careertrojan:change-me@postgres:5432/careertrojan'   --from-literal=REDIS_URL='redis://redis:6379/0'   --from-literal=SECRET_KEY='change-me'   --from-literal=CT_JWT_SECRET='change-me'   --from-literal=BRAINTREE_ENVIRONMENT='sandbox'   --from-literal=BRAINTREE_MERCHANT_ID='replace-me'   --from-literal=BRAINTREE_PUBLIC_KEY='replace-me'   --from-literal=BRAINTREE_PRIVATE_KEY='replace-me'   --from-literal=ZENDESK_WEBHOOK_SECRET='replace-me'   --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "${NAMESPACE}" create secret generic postgres-secrets   --from-literal=POSTGRES_USER='careertrojan'   --from-literal=POSTGRES_PASSWORD='change-me'   --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "${NAMESPACE}" create secret generic minio-secrets   --from-literal=MINIO_ROOT_USER='careertrojan'   --from-literal=MINIO_ROOT_PASSWORD='change-me'   --dry-run=client -o yaml | kubectl apply -f -
