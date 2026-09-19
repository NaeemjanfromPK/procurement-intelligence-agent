FROM python:3.12-slim

WORKDIR /app

# System deps for Prophet/matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Streamlit dashboard
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]