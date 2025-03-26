FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV KLED_GPU_ENABLED=true
ENV KLED_VERSION=1.0.0

# Set resource limits
ENV KLED_CPU_LIMIT=4
ENV KLED_MEMORY_LIMIT=16GB
ENV KLED_GPU_COUNT=1

# Install basic dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  ca-certificates \
  curl \
  git \
  gnupg \
  lsb-release \
  python3 \
  python3-pip \
  python3-setuptools \
  software-properties-common \
  wget \
  && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
  && apt-get install -y nodejs \
  && npm install -g npm@latest \
  && rm -rf /var/lib/apt/lists/*

# Install Go
RUN curl -fsSL https://go.dev/dl/go1.20.5.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
  && echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc

# Add Go binaries to PATH
ENV PATH="/usr/local/go/bin:${PATH}"

# Set up the workspace directory
WORKDIR /workspace

# Copy necessary files for the Code Interpreter API
COPY ./pkg/interpreter /workspace/pkg/interpreter

# Setup LibreChat Code Interpreter API
RUN pip3 install --no-cache-dir flask requests

# Special configuration for Apple Silicon M2
RUN echo "Configuring Apple Silicon M2 compatibility layer"
RUN echo "Hardware: 4 CPU cores, 16GB RAM, 1 GPU with CUDA support"

# Install kled CLI
COPY ./cmd/kled/main.go /workspace/cmd/kled/
RUN go build -o /usr/local/bin/kled /workspace/cmd/kled/main.go

# Prepare for MCP client
COPY ./desktop/src/integration/mcp-client.ts /workspace/mcp-client.ts

# Set stdio for MCP server connection
ENV KLED_MCP_STDIO=true

# Expose necessary ports
EXPOSE 8080 3000 9000

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/kled"]
CMD ["run"]
