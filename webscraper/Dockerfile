FROM python:3.11-alpine

# Installiere System-Dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Python Dependencies installieren
RUN pip install --no-cache-dir \
    requests \
    beautifulsoup4 \
    python-telegram-bot \
    lxml

# Script kopieren
COPY run.py /app/

# Ausführbar machen
RUN chmod +x /app/run.py

# Home Assistant Labels
LABEL \
    io.hass.name="Web Scraper Telegram Bot" \
    io.hass.description="Überwacht Webseiten und sendet Updates per Telegram" \
    io.hass.arch="armhf|aarch64|amd64|armv7|i386" \
    io.hass.type="addon" \
    io.hass.version="1.0.0"

# Script ausführen
CMD ["python", "/app/run.py"]
