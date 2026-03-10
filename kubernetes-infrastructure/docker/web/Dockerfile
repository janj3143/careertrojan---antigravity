FROM node:20-alpine AS build
WORKDIR /src
COPY careertrojan/apps/admin ./apps/admin
COPY careertrojan/apps/user ./apps/user
COPY careertrojan/apps/mentor ./apps/mentor
# In a real environment we would build them:
# RUN cd apps/admin && npm ci && npm run build
# RUN cd apps/user && npm ci && npm run build
# RUN cd apps/mentor && npm ci && npm run build
FROM nginx:1.27-alpine
# Copy our customized nginx configuration
COPY docker/web/nginx.conf /etc/nginx/conf.d/default.conf
# And copy the compiled UI bundles (assuming they exist or would exist in /src/apps/*/dist)
# COPY --from=build /src/apps/admin/dist /usr/share/nginx/html/admin
# COPY --from=build /src/apps/user/dist /usr/share/nginx/html/user
# COPY --from=build /src/apps/mentor/dist /usr/share/nginx/html/mentor
