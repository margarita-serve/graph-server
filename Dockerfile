FROM python:3.9-slim-buster

WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY . /app
EXPOSE 5006

ENV PYTHONUNBUFFERED=0
#ENTRYPOINT [ "python","main.py"]
CMD ["python", "app/main.py"]