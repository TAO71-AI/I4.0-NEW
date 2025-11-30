FROM python:3.11.14-slim

RUN apt-get update

# To manually edit the configuration
RUN apt-get install -y vim nano

# To automatically detect the hardware
RUN apt-get install -y pciutils mesa-utils libgl1-mesa-dev libglib2.0-dev libglib2.0-0

# Other system requirements
RUN apt-get install -y build-essential

RUN useradd --create-home --shell /bin/bash i4

WORKDIR /home/i4/Server
COPY --chown=i4:i4 . .
USER i4

RUN python requirements.py
CMD ["python", "server.py"]