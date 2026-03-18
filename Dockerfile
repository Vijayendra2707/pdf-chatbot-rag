FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ✅ Render expects this port
EXPOSE 10000

# ✅ MUST use port 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]