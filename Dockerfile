FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN mkdir -p /data
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8000
ENV HOST=0.0.0.0
ENV INTERNALOPS_DB=/data/internalops.db
ENV AI_PROVIDER_MODE=free-first

EXPOSE 8000

CMD ["python", "-m", "app.main"]
