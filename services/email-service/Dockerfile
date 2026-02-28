# =============================================================================
# CareerTrojan Email Service — Node.js Microservice
# =============================================================================
# Build:   docker build -t careertrojan-email-service ./services/email-service
# Run:     docker run -p 3050:3050 careertrojan-email-service
# =============================================================================

FROM node:18-alpine

LABEL project="CareerTrojan-Antigravity" service="email-service"

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Copy source
COPY src/ ./src/

# Create logs directory
RUN mkdir -p logs

# Environment
ENV NODE_ENV=production
ENV EMAIL_SERVICE_PORT=3050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3050/health || exit 1

EXPOSE 3050

CMD ["node", "src/index.js"]
