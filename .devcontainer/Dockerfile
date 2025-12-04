# Base Python devcontainer
FROM mcr.microsoft.com/devcontainers/python:3.12

# Until we have a mirror for GitHub releases, we can't use the latest versions
# https://datarobot.atlassian.net/browse/CFX-4255
ARG PULUMI_DATAROBOT_PLUGINVERSION=v0.10.22
ARG DR_VERSION=0.2.16

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
RUN curl -L -o /tmp/dr.tar.gz \
    https://github.com/datarobot-oss/cli/releases/download/v${DR_VERSION}/dr_v${DR_VERSION}_Linux_x86_64.tar.gz \
    && tar -xzf /tmp/dr.tar.gz -C ~/.local/bin dr \
    && chmod +x ~/.local/bin/dr \
    && rm /tmp/dr.tar.gz

# Verify installations
RUN python --version && uv --version && task --version && pulumi version && dr --version && \
    pulumi login --local


# Set working directory
WORKDIR /workspace
