# syntax=docker/dockerfile:1
FROM python:3.10.7-alpine
RUN apt-get install celery
ENV FLASK_APP=app.py
ENV FLASK_ENV=development/
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
RUN celery.sh
COPY . /app
# RUN FLASK_APP FLASK_ENV flask run
EXPOSE 5000
CMD ["flask", "--app app.py", "--debug run"]
