# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY services/ai-agents/web/package*.json ./

# Install dependencies
RUN npm install --only=production

# Copy source code
COPY services/ai-agents/web/ .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app to nginx
COPY --from=build /app/build /usr/share/nginx/html

# Copy documentation files
COPY docs /usr/share/nginx/html/docs

# Copy nginx configuration
COPY services/ai-agents/web/nginx.conf /etc/nginx/nginx.conf

# Create non-root user
RUN addgroup -g 1001 -S appuser && adduser -S appuser -u 1001 -G appuser

# Create necessary directories and set permissions
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run /tmp/nginx && \
    chown -R appuser:appuser /var/cache/nginx /var/log/nginx /var/run /tmp/nginx /usr/share/nginx/html

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
