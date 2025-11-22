# Stage 1: Build React frontend
FROM node:18 AS build-node
WORKDIR /app/frontend
# Force cache invalidation for package.json changes
ARG CACHEBUST=1
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.10-slim
WORKDIR /app

# Install backend requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend to static folder served by FastAPI
COPY --from=build-node /app/frontend/dist /app/static

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


