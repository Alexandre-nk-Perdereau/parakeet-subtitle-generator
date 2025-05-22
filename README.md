# Parakeet Subtitle Generator

Automatic subtitle generation for videos using **NVIDIA Parakeet TDT 0.6B V2** model.

## Features

- Automatic video subtitling (MP4, AVI, MOV, MKV)
- Audio file support (MP3, WAV, FLAC)
- Drag and drop interface
- SRT subtitle files
- Accurate word-level timestamps
- REST API for integration
- NVIDIA GPU acceleration

## Requirements

- **Python 3.8+**: [Download Python](https://python.org/downloads/)
- **Git**: [Download Git](https://git-scm.com/downloads)
- **Docker Desktop**: [Download Docker](https://docker.com/products/docker-desktop/)
- NVIDIA GPU with CUDA 12.x
- Recent NVIDIA drivers


## Quick Start

### 1. Clone and Setup

```bash
git clone
cd parakeet-subtitle
```

### 2. Start API (Docker)

```bash
start_docker.bat
```

### 3. Install Windows GUI

```bash
setup.bat
```

### 4. Run Application

```bash
run.bat
```