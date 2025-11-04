# Base Python devcontainer
FROM mcr.microsoft.com/devcontainers/python:3.12

ARG DR_VERSION=0.1.8

# Install GDB to enable PyCharm -> Attach to Process...
RUN apt update && apt install -y gdb

USER vscode

ENV PATH="/home/vscode/.local/bin:/home/vscode/.pulumi/bin:${PATH}"

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && uv tool install pre-commit

# Install Task (Taskfile runner)
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin

# Install Pulumi
RUN PULUMI_INSTALL_ROOT=/home/vscode/.local/bin curl -fsSL https://get.pulumi.com | sh

# TODO: install plugin directly from the plugin registry

# Install datarobot-oss CLI manually (v0.1.2)
RUN curl -L -o /tmp/dr.tar.gz \
    https://github.com/datarobot-oss/cli/releases/download/v${DR_VERSION}/dr_v${DR_VERSION}_Linux_x86_64.tar.gz \
    && tar -xzf /tmp/dr.tar.gz -C ~/.local/bin dr \
    && chmod +x ~/.local/bin/dr \
    && rm /tmp/dr.tar.gz

# Verify installations
RUN python --version && uv --version && task --version && pulumi version && dr version

# Set working directory
WORKDIR /workspace
