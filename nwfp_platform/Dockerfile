# ---------------------------------------------------------------------------
# Bhutan NWFP Digital Marketplace — Production Docker image
# Base image: python:3.12-slim (Debian Bookworm)
# ---------------------------------------------------------------------------
FROM python:3.12-slim

# ---------------------------------------------------------------------------
# System dependencies
#   gdal-bin + libgdal-dev  — GDAL CLI tools and headers for GeoDjango
#   libgeos-dev             — GEOS geometry library
#   libproj-dev             — PROJ cartographic library
#   postgresql-client       — psql, pg_dump (useful for management commands)
#   libpq-dev               — PostgreSQL client headers (required by psycopg2)
#   gcc                     — C compiler for building Python extensions
#   libmagic1               — file-type detection for python-magic
#   libffi-dev              — foreign function interface (some pip wheels need it)
# ---------------------------------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        postgresql-client \
        libpq-dev \
        gcc \
        libmagic1 \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# GDAL environment — point python-gdal at the shared library.
# The exact path is resolved at build time; adjust if the base image changes.
# ---------------------------------------------------------------------------
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so
ENV PROJ_LIB=/usr/share/proj

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---------------------------------------------------------------------------
# Working directory
# ---------------------------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------------------------
# Install Python dependencies (production layer — cached separately so that
# code changes do not invalidate this layer)
# ---------------------------------------------------------------------------
COPY requirements/base.txt requirements/base.txt
COPY requirements/production.txt requirements/production.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements/production.txt

# ---------------------------------------------------------------------------
# Copy application source
# ---------------------------------------------------------------------------
COPY . .

# ---------------------------------------------------------------------------
# Collect static files
# ---------------------------------------------------------------------------
RUN python manage.py collectstatic --noinput --settings=config.settings.production

# ---------------------------------------------------------------------------
# Non-root user for security
# ---------------------------------------------------------------------------
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--config", "gunicorn.conf.py"]
