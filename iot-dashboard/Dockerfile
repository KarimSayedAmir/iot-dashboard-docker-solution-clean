FROM node:20-alpine as build

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies with legacy peer deps and clean npm cache
RUN npm install --legacy-peer-deps && \
    npm cache clean --force

# Copy the rest of the application
COPY . .

# Set environment variables
ENV NODE_ENV=production
ENV VITE_API_URL=http://backend:3000/api

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create uploads directory
RUN mkdir -p /usr/share/nginx/html/uploads && \
    chmod 777 /usr/share/nginx/html/uploads

# Expose port
EXPOSE 80

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://localhost:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]
