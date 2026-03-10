#!/usr/bin/env bash
set -euo pipefail
NS="${1:-careertrojan}"
kubectl -n "$NS" port-forward svc/backend-api 8600:80 &
kubectl -n "$NS" port-forward svc/web 8080:80 &
wait

