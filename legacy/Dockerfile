FROM python:3.10-slim
WORKDIR /app

RUN pip install --no-cache-dir pika

COPY . .

# Default: keep container alive (reader is invoked via API or manually)
CMD ["tail", "-f", "/dev/null"]