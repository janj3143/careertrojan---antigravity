# =============================================================================
# CareerTrojan User Portal — Multi-stage Dockerfile
# =============================================================================
# Build:   docker build -t careertrojan-user ./apps/user
# Run:     docker run -p 8502:80 careertrojan-user
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

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx config (use project config if present, else default)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
