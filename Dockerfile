FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data
# Add backend to PYTHONPATH so imports like 'database' work
ENV PYTHONPATH=/app/app/backend

# Create data directory
RUN mkdir -p /data

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8273

# Command to run the application
# We run main:app because app/backend is in PYTHONPATH
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8273"]

