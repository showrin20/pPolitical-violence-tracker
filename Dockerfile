FROM python:3.11-slim

WORKDIR /app

# Copy backend code into /app/backend
COPY backend /app/backend

# Copy frontend code into /app/frontend
COPY frontend /app/frontend

# Install dependencies from backend/requi rements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Install Playwright browsers (Chromium, Firefox, WebKit)
RUN playwright install chromium

# Expose port
EXPOSE 8000

# Set working directory to backend to run uvicorn
WORKDIR /app/backend

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
