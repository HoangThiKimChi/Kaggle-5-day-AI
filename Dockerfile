FROM python:3.11-slim

# Prevent python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
# Set the port for Hugging Face Spaces (defaults to 7860)
ENV PORT=7860

WORKDIR /app

# Install system dependencies if needed (none required for genai SDK)
# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and reference files
COPY scripts/ ./scripts/
COPY references/ ./references/

# Expose Hugging Face Space port
EXPOSE 7860

# Run the FastAPI server
CMD ["python3", "scripts/server.py"]
