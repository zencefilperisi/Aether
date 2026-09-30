# Aether -- multi-stage build.
# Stage 1 compiles the Rust core (aether_core_rs) with maturin.
# Stage 2 is a slim runtime image carrying only what the CLI needs.

# ---- Stage 1: build the Rust extension ------------------------------------
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install the Rust toolchain.
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN pip install --no-cache-dir maturin

WORKDIR /build
COPY core/chaos/aether_core_rs/ ./aether_core_rs/
# Build a wheel for the extension so it can be installed into the runtime image.
RUN cd aether_core_rs && maturin build --release --out /wheels

# ---- Stage 2: runtime -----------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Python deps (no GUI extras needed for the CLI in a container).
COPY requirements.txt .
RUN pip install --no-cache-dir \
        numpy scipy requests python-dotenv cryptography pytest

# Install the compiled Rust core from the wheel built in stage 1.
COPY --from=builder /wheels/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Application code.
COPY aether.py aether_benchmarks.py ./
COPY core/ ./core/
COPY utility/ ./utility/
COPY tests/ ./tests/

# Default: show the CLI help. Override with e.g.
#   docker run --rm aether python aether.py --gen-key
ENTRYPOINT ["python"]
CMD ["aether.py", "--help"]
