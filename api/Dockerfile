FROM python:3.8

WORKDIR /app

COPY ./dist/api-0.1.0-py3-none-any.whl /app

RUN pip install /app/api-0.1.0-py3-none-any.whl

EXPOSE 8080

ENTRYPOINT [ "api" ]
