FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    wget \
    curl \
    git \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip3 install --upgrade pip

RUN pip3 install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

RUN pip3 install \
    nemo_toolkit[asr]==2.3.0 \
    fastapi==0.115.6 \
    uvicorn==0.34.0 \
    python-multipart==0.0.20 \
    librosa==0.10.2.post1 \
    soundfile==0.13.1 \
    pydub==0.25.1

COPY api/ .

RUN python3 -c "import nemo.collections.asr as nemo_asr; nemo_asr.models.ASRModel.from_pretrained('nvidia/parakeet-tdt-0.6b-v3')"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]