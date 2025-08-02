# ---- Builder Stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Upgrade pip and install dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheels -r requirements.txt


# ---- Final Stage ----
# This stage creates the final, lean production image.
FROM python:3.11-slim

# Create a non-root user and group for security
RUN addgroup --system app && adduser --system --group app

# Create a directory for error output and set permissions.
# This path must match the volume mount in docker-compose.yml and the
# ERROR_ARTIFACTS_DIR environment variable.
WORKDIR /app
RUN mkdir -p /app/errors && chown -R app:app /app/errors

# Copy installed dependencies (wheels) from the builder stage
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY main.py .

# Set ownership of the app directory to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Command to run the application
CMD ["python", "main.py"]
