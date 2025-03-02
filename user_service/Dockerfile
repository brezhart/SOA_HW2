FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Добавляем ожидание готовности БД
RUN apt-get update && apt-get install -y netcat-traditional
COPY wait-for-postgres.sh .
RUN chmod +x wait-for-postgres.sh

CMD ["./wait-for-postgres.sh", "postgres", "5432", "--", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
