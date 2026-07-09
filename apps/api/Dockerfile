FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY packages/contracts packages/contracts
COPY apps/api apps/api

RUN pip install --no-cache-dir -e packages/contracts -e apps/api

WORKDIR /app/apps/api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

