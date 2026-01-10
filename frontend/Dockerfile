# Frontend Dockerfile - Multi-stage build for React/Vite application

# Stage 1: Build the application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for better caching
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build arguments for environment variables at build time
ARG VITE_API_URL=
ARG VITE_SENTRY_DSN=
ARG VITE_ENVIRONMENT=production

# Set environment variables for build
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_SENTRY_DSN=${VITE_SENTRY_DSN}
ENV VITE_ENVIRONMENT=${VITE_ENVIRONMENT}

# Build the application
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
