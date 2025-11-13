FROM python:3.11.14-slim

RUN apt-get update
RUN apt-get install -y vim nano
RUN useradd --create-home --shell /bin/bash i4

WORKDIR /home/i4/Server
COPY --chown=i4:i4 . .
USER i4

RUN python requirements.py
CMD ["python", "server.py"]