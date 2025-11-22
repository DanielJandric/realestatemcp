# Root-level Dockerfile to support Render service using build context "."
# Builds React app from my-ai-app/frontend and serves via FastAPI from my-ai-app/backend

# Stage 1: Build React frontend
FROM node:18 AS build-node
WORKDIR /app/frontend
COPY my-ai-app/frontend/package*.json ./
RUN npm install
COPY my-ai-app/frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.10-slim
WORKDIR /app

# Install backend requirements
COPY my-ai-app/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY my-ai-app/backend/ .

# Copy built frontend to static folder served by FastAPI
COPY --from=build-node /app/frontend/dist /app/static

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


