# syntax=docker/dockerfile:1

# ── Build stage ───────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (layer-cache friendly).
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build.
COPY . .
RUN npm run build

# ── Runtime stage — nginx ─────────────────────────────────────────────────────
FROM nginx:alpine

# Remove the default nginx config and replace with our own.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built assets from the builder stage.
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 5173

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:5173/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
