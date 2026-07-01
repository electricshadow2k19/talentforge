FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY app/data ./app/data
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts ./scripts

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python scripts/seed.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
