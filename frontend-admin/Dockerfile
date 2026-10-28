# ── Build stage ───────────────────────────────────────────────────────────────
# Context is the monorepo root so ui-shared is available.
FROM node:20-alpine AS builder

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy workspace manifests and lockfile for layer-cache-friendly install.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
COPY ui-shared/package.json ./ui-shared/
COPY frontend-admin/package.json ./frontend-admin/

RUN pnpm install --frozen-lockfile

# Copy all source needed for the build.
COPY ui-shared/ ./ui-shared/
COPY frontend-admin/ ./frontend-admin/

WORKDIR /app/frontend-admin
RUN pnpm run build:docker

# ── Runtime stage — nginx ─────────────────────────────────────────────────────
FROM nginx:alpine

COPY frontend-admin/nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/frontend-admin/dist /usr/share/nginx/html

EXPOSE 5174

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:5174/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
