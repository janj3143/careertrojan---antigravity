# =============================================================================
# CareerTrojan Admin Portal — Multi-stage Dockerfile
# =============================================================================
# Build:   docker build -t careertrojan-admin ./apps/admin
# Run:     docker run -p 8501:80 careertrojan-admin
# =============================================================================

# ── Build Stage ──────────────────────────────────────────────────────────
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies first (layer cache)
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline

# Copy source and build
COPY . .
RUN npm run build

# ── Production Stage ─────────────────────────────────────────────────────
FROM nginx:alpine

LABEL project="CareerTrojan-Antigravity" service="admin-portal"

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]