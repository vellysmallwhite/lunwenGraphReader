FROM python:3.11-slim

WORKDIR /app

# If you add requirements.txt later, uncomment below
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

CMD ["python", "app.py"]

