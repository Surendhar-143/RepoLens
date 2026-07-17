FROM node:20-alpine AS base

WORKDIR /app

COPY package.json ./

RUN npm install

COPY . .

# Expose dev/preview port
EXPOSE 3000

# Default command runs dev server in container
CMD ["npm", "run", "dev", "--", "--host"]
