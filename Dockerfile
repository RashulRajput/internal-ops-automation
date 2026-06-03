FROM python:3.11-slim

WORKDIR /app

# Copy source
COPY . .

# Create persistent data directory
RUN mkdir -p /data

# Port — overridden by Railway/Render at runtime
ENV PORT=8000
ENV HOST=0.0.0.0
ENV INTERNALOPS_DB=/data/internalops.db

EXPOSE 8000

CMD ["python", "-m", "app.main"]
