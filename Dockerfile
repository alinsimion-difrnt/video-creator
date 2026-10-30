# explainer-video-creator: pipeline image for GitHub Actions (ADR 0003).
# ffmpeg + the lens CLI with its audio/vision deps (CPU-only torch, faster-whisper, demucs, rapidocr).
# Keep the image well under ~6 GB (private runners have a 14 GB disk); model weights are cached separately.
# Run with the repo checkout mounted at /work: docker run --rm -v "$PWD:/work" <image> validate --all
FROM python:3.12-slim-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app
COPY pyproject.toml uv.lock .python-version README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY lens ./lens
RUN uv sync --frozen --no-dev

ENV LENS_ROOT=/work
WORKDIR /work
ENTRYPOINT ["lens"]
CMD ["--help"]
