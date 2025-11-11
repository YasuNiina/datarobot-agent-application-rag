# Base Python devcontainer
FROM mcr.microsoft.com/devcontainers/python:3.12

ARG PULUMI_DATAROBOT_PLUGINVERSION=v0.10.22

# Install GDB to enable PyCharm -> Attach to Process...
RUN apt update && apt install -y gdb

USER vscode

ENV PATH="/home/vscode/.local/bin:/home/vscode/.pulumi/bin:${PATH}"

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && uv tool install pre-commit

# Install Task (Taskfile runner)
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin

# Install Pulumi
RUN PULUMI_INSTALL_ROOT=/home/vscode/.local/bin curl -fsSL https://get.pulumi.com | sh  && \
    pulumi plugin install resource datarobot ${PULUMI_DATAROBOT_PLUGINVERSION} --server https://github.com/datarobot-community/pulumi-datarobot/releases/download/${PULUMI_DATAROBOT_PLUGINVERSION}/

ENV PULUMI_SKIP_UPDATE_CHECK=true

# Install dr CLI
RUN curl https://cli.datarobot.com/install | sh

# Verify installations
RUN python --version && uv --version && task --version && pulumi version && dr version

# Set working directory
WORKDIR /workspace
