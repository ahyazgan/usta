# Usta backend — üretim imajı (FastAPI + uvicorn)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Bağımlılıklar (katman önbelleği için önce requirements)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodu + prompt'lar
COPY app ./app
COPY prompts ./prompts

# Render/Fly $PORT enjekte eder; yoksa 8080.
ENV PORT=8080
EXPOSE 8080

# Tek worker yeterli (MVP). Sağlık: GET /health
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
