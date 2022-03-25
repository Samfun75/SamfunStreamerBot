# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10.4-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install FFmpeg static builds
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl xz-utils && rm -rf /var/lib/apt/lists/*
RUN curl https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz -L --silent --fail --retry 5 --retry-max-time 15 -o ffmpeg.tar.xz
RUN tar xJf ffmpeg.tar.xz --strip-components=1
RUN mv -f ffmpeg ffprobe /usr/local/bin/

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

CMD ["python", "-m", "streamer"]
