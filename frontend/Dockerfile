FROM node:22-alpine

WORKDIR /app

# Dependencies are cached until package.json or package-lock.json changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# Polling keeps hot reload reliable with Docker bind mounts.
ENV CHOKIDAR_USEPOLLING=true

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
