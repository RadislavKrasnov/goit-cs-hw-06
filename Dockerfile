FROM python:3.10

ENV APP_HOME /app

WORKDIR $APP_HOME

COPY . .

RUN pip install pymongo

EXPOSE 3000
EXPOSE 5000

ENTRYPOINT ["python", "main.py"]
