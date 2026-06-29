# Stage 1: Build the React application
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies first to leverage Docker layer caching
COPY package.json package-lock.json ./
RUN npm install

# Copy source code and build the production assets
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy the build output from the previous stage to Nginx's public folder
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80 for the outside world
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]