FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Expose port (package.jsonで3030を使用)
EXPOSE 3030

# Development command
CMD ["npm", "run", "dev"]
