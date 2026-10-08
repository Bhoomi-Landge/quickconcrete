# Build React frontend, then serve API + SPA with Gunicorn (Render / Railway).
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY --from=frontend /frontend/dist /app/frontend/dist

WORKDIR /app/backend
ENV SERVE_FRONTEND=1
ENV PYTHONUNBUFFERED=1

EXPOSE 10000
CMD gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 120 app:app
