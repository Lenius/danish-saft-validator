# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG=da_DK.UTF-8 \
    LC_ALL=da_DK.UTF-8

# Systempakker til lxml/cryptography m.m.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    libffi-dev libssl-dev \
    libxml2-dev libxslt1-dev \
    locales tzdata \
 && sed -i 's/# da_DK.UTF-8 UTF-8/da_DK.UTF-8 UTF-8/' /etc/locale.gen \
 && locale-gen \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installer Python-krav først (cachevenligt)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiér resten af projektet
COPY . /app

# Persistente mapper
RUN mkdir -p /app/config /work

# Non-root bruger (pænere filrettigheder på host-volumes)
RUN useradd -m appuser && chown -R appuser:appuser /app /work
USER appuser

# Entrypoint, der bevarer/brug config.ini og understøtter XML_PATH
COPY docker/entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh && chown appuser:appuser /entrypoint.sh
USER appuser

# Miljø-variabler til non-interaktiv kørsel
ENV XML_PATH="" \
    CONFIG_LANG="dk" \
    CONFIG_RESET="0"

# Mapper til data & config (host-mounts)
VOLUME ["/work", "/app/config"]

ENTRYPOINT ["/entrypoint.sh"]
