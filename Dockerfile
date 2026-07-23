FROM python:3.11-slim-bookworm

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    wget \
    build-essential \
    libffi-dev \
    libssl-dev \
    libopus-dev \
    libopus0 \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libwebp-dev \
    neofetch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root/LadyRezebb

COPY requirements.txt .
RUN pip install -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "-m", "MukeshRobot"]
