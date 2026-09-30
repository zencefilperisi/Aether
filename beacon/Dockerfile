# Aether Randomness Beacon -- API + worker image.
#
# Two-stage build: stage 1 compiles the Aether Rust core into a wheel so the
# beacon can use the real chaotic entropy engine; stage 2 is the runtime.
# If you don't need the Rust core, the beacon runs on the os.urandom fallback
# and you can skip straight to a single-stage python:3.12-slim build.

FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN pip install --no-cache-dir maturin
WORKDIR /build
# The Aether core lives in the repo root; build context is the repo root.
COPY core/chaos/aether_core_rs/ ./aether_core_rs/
RUN cd aether_core_rs && maturin build --release --out /wheels || echo "core build skipped"

FROM python:3.12-slim AS runtime
WORKDIR /app

COPY beacon/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the Aether core wheel if it was built (optional).
COPY --from=builder /wheels/ /tmp/wheels/
RUN pip install --no-cache-dir /tmp/wheels/*.whl 2>/dev/null || echo "running without Aether core"

# Aether engine sources (so beacon.entropy can import NIHDE) + beacon app.
COPY core/ ./core/
COPY beacon/ ./beacon/

WORKDIR /app/beacon
EXPOSE 8000
# Default command runs the API; the worker overrides this in compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
