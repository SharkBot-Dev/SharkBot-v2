FROM python:3.11-slim

WORKDIR /app

RUN pip install flask gunicorn matplotlib numpy sympy

RUN useradd -m appuser
USER appuser

COPY main.py .

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--timeout", "5"]