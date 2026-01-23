FROM python:3.14

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg open-jtalk open-jtalk-mecab-naist-jdic

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]