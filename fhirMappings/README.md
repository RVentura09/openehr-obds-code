# Template for mapping openEHR structures to fhir

This repo hosts a template project for mapping json structures (e.g. openEHR) to FHIR using Python.
It is intended for the export of MII-KDS-Data to a FHIR-Server.

## Build and Run the project

Before building and running the environment varibles have to be set. This can be done in the `.env` file. Durring the build of the container the variables are also taken from there `.env`. The file given provides the current default values for running the file locally. 

The easiest way to build and deploy is to `cd` into the project dir and run 
```sh
docker compose up
```
This first builds the images and then deployes a container.
```sh
docker compose down --rmi local
```
can be used to remove the container and also the local image. If the image already exists it isn't build again with the next `docker compose up`.

The kafka_consumer can also be run with locally with
```sh
python3 app/kafka_consumer.py
```
from the root of the project (can slighly vary with regard to the platform). In that case there needs to be a python environment active that provides all the necessary dependencies. These can be found in the `python_env.yml`.

If youn want to run it locally note, that there needs to be kafka-broker for the consumer to connect to. A lokal kafka instance can be run easly with docker as well.
```sh
docker run -p 9092:9092 --name broker apache/kafka:latest
```

For more detailed documentation please see https://wiki.medicsh.de/display/MEDIC/Template+for+mapping+openEHR-structures+to+FHIR