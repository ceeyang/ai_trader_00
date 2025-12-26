FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Environment setup (User can override these)
ENV PYTHONUNBUFFERED=1

CMD ["python", "run.py"]
