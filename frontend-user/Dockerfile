# syntax=docker/dockerfile:1

# ── Build stage ───────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

# Enable corepack so pnpm is available inside the build container.
RUN corepack enable

WORKDIR /app

# Install dependencies first (layer-cache friendly).
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# Copy source and build.
COPY . .
RUN pnpm build

# ── Runtime stage — nginx ─────────────────────────────────────────────────────
FROM nginx:alpine

# Remove the default nginx config and replace with our own.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built assets from the builder stage.
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]
