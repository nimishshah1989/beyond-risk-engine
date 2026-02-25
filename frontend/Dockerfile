FROM node:20-slim

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy source and build
COPY . .
RUN npm run build

# Verify dist was created
RUN ls -la dist/

# Serve the built app
CMD ["node", "server.js"]
