# Stage 1: Build production React bundle
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install --no-audit --prefer-offline

# Copy frontend source code
COPY . .

# Build Vite SPA with production assets
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Stage 2: Serve via Caddy 2 reverse proxy
FROM caddy:2-alpine

# Copy built frontend assets
COPY --from=builder /app/dist /srv/frontend/dist

# Copy Caddyfile reverse proxy configuration
COPY Caddyfile /etc/caddy/Caddyfile

EXPOSE 80 443

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
