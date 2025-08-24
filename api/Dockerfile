FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN uv venv && uv pip install -e .

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run the application with virtual environment activated
CMD ["/bin/bash", "-c", "source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
