FROM node:20-alpine

WORKDIR /app

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies and clean npm cache
RUN npm install --omit=dev && \
    npm cache clean --force

# Copy the rest of the application
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p data uploads && \
    chown -R node:node /app

# Switch to non-root user
USER node

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Expose port
EXPOSE 3000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:3000/health || exit 1

# Start the application
CMD ["node", "server.js"]
