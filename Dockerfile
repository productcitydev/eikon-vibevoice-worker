FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg libsndfile1 git \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN git clone --depth 1 https://github.com/microsoft/VibeVoice.git /vibevoice-src
ENV PYTHONPATH=/vibevoice-src

RUN mkdir -p /voices && \
    cp /vibevoice-src/demo/voices/streaming_model/*.pt /voices/

RUN cd /tmp && \
    apt-get update && apt-get install -y wget && \
    wget -q https://github.com/user-attachments/files/24189272/experimental_voices_en1.tar.gz && \
    wget -q https://github.com/user-attachments/files/24189273/experimental_voices_en2.tar.gz && \
    tar --no-same-owner -xzf experimental_voices_en1.tar.gz -C /voices/ && \
    tar --no-same-owner -xzf experimental_voices_en2.tar.gz -C /voices/ && \
    rm -f *.tar.gz && \
    rm -rf /var/lib/apt/lists/*

COPY scripts/ /scripts/
COPY handler.py audition.py batch.py .

ENV SCRIPT=handler.py
CMD ["sh", "-c", "python3 $SCRIPT"]
