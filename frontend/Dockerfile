FROM node:20-alpine

WORKDIR /app

# Install dependencies (npm ci for reproducible builds)
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -S appuser && adduser -S appuser -G appuser \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3030

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget --spider -q http://localhost:3030 || exit 1

# Development command
CMD ["npm", "run", "dev"]
