FROM python:3.10-slim
LABEL authors="mks_min"

# Установка poetry
ENV POETRY_VERSION=2.1.1
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /atombot

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi --only main

COPY . .

RUN chmod +x ./config/prestart.sh

ENTRYPOINT ["./config/prestart.sh"]

CMD ["python", "-u", "run.py"]