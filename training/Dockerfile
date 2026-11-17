FROM python:3.11-slim
ARG INSTALL_NEMO=0
ARG INSTALL_BITSANDBYTES=0
ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git curl build-essential libsndfile1 nodejs npm && npm install -g configurable-http-proxy && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip setuptools wheel && pip install -r /tmp/requirements.txt && if [ "$INSTALL_NEMO" = "1" ]; then pip install "nemo_toolkit[asr]>=2.0,<3"; fi && if [ "$INSTALL_BITSANDBYTES" = "1" ]; then pip install "bitsandbytes>=0.45,<1"; fi
COPY jupyterhub_config.py /etc/jupyterhub/jupyterhub_config.py
RUN mkdir -p /srv/jupyterhub /workspace/notebooks /workspace/workspace
EXPOSE 8000
CMD ["jupyterhub","-f","/etc/jupyterhub/jupyterhub_config.py"]
