FROM python:3

COPY . /

RUN pip install pipenv && \
    pipenv install --deploy --system --ignore-pipfile