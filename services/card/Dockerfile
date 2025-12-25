FROM python:3.11-slim

RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY services/card/ /app/

EXPOSE 8002

CMD ["gunicorn", "-b", "0.0.0.0:8002", "-w", "4", "app:create_app()"]
