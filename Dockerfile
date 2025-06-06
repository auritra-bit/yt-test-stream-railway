FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

WORKDIR /app

COPY . .

# ✅ Give executable permission to start.sh
RUN chmod +x start.sh

RUN pip install -r requirements.txt

CMD ["./start.sh"]
