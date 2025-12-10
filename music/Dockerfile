FROM python:3.11-slim

RUN apt update && apt install -y ffmpeg && apt clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY .env .

CMD ["python", "main.py"]