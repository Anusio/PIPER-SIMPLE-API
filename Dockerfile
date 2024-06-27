FROM nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-dev \
    curl \
    ca-certificates \
    ffmpeg \
    libespeak1

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1

WORKDIR /usr/src

RUN pip install --upgrade pip

COPY ./requirements.txt .

RUN pip install nvidia-pyindex

RUN pip install --no-cache-dir -r requirements.txt

RUN rm requirements.txt

COPY ./ .

ENV HOST=0.0.0.0
ENV PORT=5501

CMD ["python", "main.py"]
