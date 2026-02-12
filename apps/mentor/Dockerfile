# =============================================================================
# CareerTrojan Mentor Portal — Multi-stage Dockerfile
# =============================================================================
# Build:   docker build -t careertrojan-mentor ./apps/mentor
# Run:     docker run -p 8503:80 careertrojan-mentor
# =============================================================================

# ── Build Stage ──────────────────────────────────────────────────────────
FROM node:18-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline

COPY . .
RUN npm run build

# ── Production Stage ─────────────────────────────────────────────────────
FROM nginx:alpine

LABEL project="CareerTrojan-Antigravity" service="mentor-portal"

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
