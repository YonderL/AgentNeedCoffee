FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source code
COPY src/ src/

# Expose port for FastAPI server
EXPOSE 8000

# Default command
CMD ["uvicorn", "agent_need_coffee.server:app", "--host", "0.0.0.0", "--port", "8000"]
