# syntax=docker/dockerfile:1
FROM python:3.10.7
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["flask", "run"]
