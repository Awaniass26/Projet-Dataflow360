# ============================================================
# DataFlow360 Frontend - Multi-stage Dockerfile
# Stage 1: Build the React application
# Stage 2: Serve static files with Nginx
# ============================================================

# ---------- Stage 1: Build ----------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY package.json package-lock.json* ./

# Install dependencies
# On utilise npm install (pas npm ci) car package-lock.json
# n'est pas forcément présent au premier build
RUN npm install

# Copy the rest of the source code
COPY . .

# Build argument for API URL (can be overridden at build time)
# IMPORTANT : les variables VITE_ sont injectées au moment du BUILD
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the production bundle
RUN npm run build

# ---------- Stage 2: Production ----------
FROM nginx:1.27-alpine AS production

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
