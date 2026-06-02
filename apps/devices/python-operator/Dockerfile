FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for compiling certain python hooks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install the core Kubernetes and MQTT steering clients
RUN pip install --no-cache-dir \
    kubernetes==30.1.0 \
    paho-mqtt==1.6.1

COPY esp32_operator.py .

CMD ["python", "-u", "esp32_operator.py"]