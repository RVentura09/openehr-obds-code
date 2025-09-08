FROM debian:12-slim AS build
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3-venv gcc libpython3-dev && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel

FROM build AS build-venv
COPY requirements.txt /requirements.txt
RUN /venv/bin/pip install --disable-pip-version-check -r /requirements.txt

FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=build-venv /venv /venv
COPY ./app/kafka_consumer.py /app/
COPY ./app/mappings/helper_functions.py /app/mappings/helper_functions.py
COPY ./app/mappings/mapping_* /app/mappings/
WORKDIR /app
ENTRYPOINT ["/venv/bin/python3", "kafka_consumer.py"]
