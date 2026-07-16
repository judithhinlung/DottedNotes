FROM python:3.11-slim-bullseye

# Install LilyPond
RUN apt-get update && apt-get install -y --no-install-recommends \
    lilypond \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project configuration and code
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package and its dependencies
RUN pip install --no-cache-dir .

EXPOSE 10000

CMD ["uvicorn", "dottednotes.web:app", "--host", "0.0.0.0", "--port", "10000"]
