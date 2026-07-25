FROM python:3.11-slim-bookworm

# Install LilyPond 2.26.0 from the official upstream binary release.
# Debian bookworm's apt package lags behind (2.24.x), so we fetch the
# self-contained upstream tarball instead of `apt-get install lilypond`.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -sSL -o /tmp/lilypond.tar.gz \
    https://gitlab.com/lilypond/lilypond/-/releases/v2.26.0/downloads/lilypond-2.26.0-linux-x86_64.tar.gz \
    && tar -xzf /tmp/lilypond.tar.gz -C /opt \
    && rm /tmp/lilypond.tar.gz \
    && ln -s /opt/lilypond-2.26.0/bin/lilypond /usr/local/bin/lilypond \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project configuration and code
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package and its dependencies
RUN pip install --no-cache-dir .

EXPOSE 10000

CMD ["uvicorn", "dottednotes.web:app", "--host", "0.0.0.0", "--port", "10000"]
