# syntax=docker/dockerfile:1

FROM python:3.10.8-buster

WORKDIR /flaskr

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


COPY requirements.txt .
RUN pip install -r requirements.txt

COPY flaskr .
RUN mkdir ../archivos_audio

EXPOSE 80

CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]

#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0","--port=80"]