# Multi-stage Dockerfile for a production-friendly Python Discord bot
FROM python:3.11-slim as base

# Allow build-time selection of non-root user
ARG USER=bot
ARG UID=1000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential git curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd --create-home --uid $UID $USER || true
WORKDIR /home/$USER/app

# Copy only requirements first for better cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Ensure files are owned by the non-root user
RUN chown -R $USER:$USER /home/$USER/app
USER $USER

# Default command — run the bot
CMD ["python", "-m", "bot"]
