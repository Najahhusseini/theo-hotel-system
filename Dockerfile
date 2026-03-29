FROM python:3.11-slim  
  
WORKDIR /app  
  
ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1  
ENV PYTHONPATH=/app  
  
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev netcat-openbsd && rm -rf /var/lib/apt/lists/*  
  
COPY requirements.txt .  
  
RUN pip install --no-cache-dir -r requirements.txt  
  
COPY . .  
  
RUN useradd -m -u 1000 theo && chown -R theo:theo /app  
  
USER theo  
  
EXPOSE 8000  
  
CMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\", \"--reload\"] 
