# Build stage for frontend assets
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./
COPY vite.config.mjs ./

# Install dependencies (skip postinstall build)
RUN npm ci --ignore-scripts

# Copy assets and build
COPY assets/ ./assets/
RUN npm run build

# Production stage
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies using uv
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY main.py .
COPY README.md .
COPY content.md .

# Copy built static files from builder
COPY --from=builder /app/static/ ./static/

# Expose the port
EXPOSE 5001

# Run the application
CMD ["python", "main.py", "5001"]
