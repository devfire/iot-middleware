![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/devfire/iot-middleware?style=for-the-badge)

# iot-middleware

## Overview
The purpose of this project is to accept sensor data from multiple sources and route them to multiple destinations.

At the moment, the only way to get data into the router is via UDP unicast.

For a detailed overview, please see the diagram below.

## Architecture

## Configuration
The main configuration file is [settings.ini](settings.ini).

It contains a list of MAC addresses and their [blynk.io](https://blynk.io) virtual pins.

Technically, this file is needed for blynk only but if you are not using blynk, then this doesn't do a whole lot more at the moment. :)

### Logging
The software uses the standard pythong logging framework. 

Default is DEBUG, to override set the environment variable like this:
```bash
export LOGLEVEL=INFO
```

### Running
There are two ways to run this software, as a python script or as a docker container.

#### Python script
The project uses `pipenv` to manage dependencies.

If you would like to run this as a python script, first initialize pipenv

```bash
pipenv shell
```

and then run it as usual

```bash
python3 processor.py
```

just make sure you set the environment variables first.

#### Docker container
If you would like to run this as a docker container (preferred way), execute the following

```bash
docker run --env-file=env.list -p 3333:3333/udp devfire/iot-middleware:latest
```

Note the `env.list` passed as a parameter. It contains the environment variables required to run the container, like so

```bash
BLYNK_AUTH=asdflkj23049
BLYNK_URL=http://blynk-cloud.com
```