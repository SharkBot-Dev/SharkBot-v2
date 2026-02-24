FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y fonts-noto-cjk
RUN pip install flask gunicorn matplotlib numpy sympy

RUN useradd -m appuser
USER appuser

COPY main.py .

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--timeout", "5"]