<p align="center">
  <a href="https://github.com/datarobot-community/datarobot-agent-application">
    <img src="./.github/datarobot_logo.avif" width="600px" alt="DataRobot Logo"/>
  </a>
</p>
<p align="center">
    <span style="font-size: 1.5em; font-weight: bold; display: block;">DataRobot Agentic Workflow Application Template</span>
</p>

<p align="center">
  <a href="https://datarobot.com">Homepage</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/index.html">Documentation</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html">Support</a>
</p>

<p align="center">
  <a href="https://github.com/datarobot-community/datarobot-agent-application/tags">
    <img src="https://img.shields.io/github/v/tag/datarobot-community/datarobot-agent-application?label=version" alt="Latest Release">
  </a>
  <a href="/LICENSE">
    <img src="https://img.shields.io/github/license/datarobot-community/datarobot-agent-application" alt="License">
  </a>
</p>

This repository provides a ready-to-use application template for building and deploying agentic workflows with
multi-agent frameworks, a fastapi backend server, a react frontend, and an MCP server. The template
streamlines the process of setting up new workflows with minimal configuration requirements.
They support local development and testing, as well as one-command deployments to production environments
within DataRobot.

```diff
-IMPORTANT: This repository updates frequently. Make sure to update your
-local branch regularly to obtain the latest changes.
```

---

# Table of contents

- [Installation](#installation)
- [Create and deploy your agent](#create-and-deploy-your-agent)
- [Develop your agent](#develop-your-agent)
- [Get help](#get-help)


# Installation

```diff
-IMPORTANT: This repository is only compatible with macOS and Linux operating systems.
```

> If you are using Windows, consider using a [DataRobot codespace](https://docs.datarobot.com/en/docs/workbench/wb-notebook/codespaces/index.html), Windows Subsystem for Linux (WSL), or a virtual machine running a supported OS.

Ensure you have the following tools installed and on your system at the required version (or newer).
It is **recommended to install the tools system-wide** rather than in a virtual environment to ensure they are available in your terminal session.

## Prerequisite tools

The following tools are required to install and run the agent application template.
For detailed installation instructions, see [Installation instructions](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-install.html#installation-instructions) in the DataRobot documentation.

| Tool         | Version    | Description                     | Installation guide            |
|--------------|------------|---------------------------------|-------------------------------|
| **dr-cli**   | >= 0.1.8  | The DataRobot CLI.                   | [dr-cli installation guide](https://github.com/datarobot-oss/cli?tab=readme-ov-file#installation) |
| **git**      | >= 2.30.0  | A version control system.       | [git installation guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) |
| **uv**       | >= 0.6.10  | A Python package manager.       | [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)     |
| **Pulumi**   | >= 3.163.0 | An Infrastructure as Code tool. | [Pulumi installation guide](https://www.pulumi.com/docs/iac/download-install/)        |
| **Taskfile** | >= 3.43.3  | A task runner.                  | [Taskfile installation guide](https://taskfile.dev/docs/installation)                 |

> **IMPORTANT**: You will also need a compatible C++ compiler and build tools installed on your system to compile some Python packages.


## Develop your agent

Once setup is complete, you are ready customize your agent, allowing you to add your own logic and functionality to the agent.
See the following documentation for more details:

- [Customize your agent](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-development.html)
- [Add tools to your agent](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-tools-integrate.html)
- [Configure LLM providers](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-llm-providers.html)
- [Use the agent CLI](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-cli-guide.html)
- [Add Python requirements](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-python-packages.html)

# Get help

If you encounter issues or have questions, try the following:

- [Contact DataRobot](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html) for support.
- Open an issue on the [GitHub repository](https://github.com/datarobot-community/datarobot-agent-application).
