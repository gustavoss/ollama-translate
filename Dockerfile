FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt app.py ./
RUN pip install -r requirements.txt

EXPOSE 5001
ENV GRADIO_SERVER_NAME="0.0.0.0" \
    GRADIO_SERVER_PORT="5001"

CMD ["python", "app.py"]
