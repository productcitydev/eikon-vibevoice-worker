FROM registry.runpod.net/jords1755-vibevoice-main-dockerfile:abf3c5875

COPY handler.py /handler.py

CMD ["python", "/handler.py"]
