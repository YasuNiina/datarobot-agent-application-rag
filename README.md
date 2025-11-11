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
- [Run your agent](#run-your-agent)
- [Develop your agent](#develop-your-agent)
- [Deploy your agent](#deploy-your-agent)
- [Get help](#get-help)


# Installation

```diff
-IMPORTANT: This repository is only compatible with macOS and Linux operating systems.
```

> If you are using Windows, consider using a [DataRobot codespace](https://docs.datarobot.com/en/docs/workbench/wb-notebook/codespaces/index.html), Windows Subsystem for Linux (WSL), or a virtual machine running a supported OS.

## Prerequisite tools

Ensure you have the following tools installed and on your system at the required version (or newer).
It is **recommended to install the tools system-wide** rather than in a virtual environment to ensure they are available in your terminal session.

The following tools are required to install and run the agent application template.
For detailed installation instructions, see [Installation instructions](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-install.html#installation-instructions) in the DataRobot documentation.

| Tool         | Version    | Description                     | Installation guide            |
|--------------|------------|---------------------------------|-------------------------------|
| **dr-cli**   | >= 0.1.8   | The DataRobot CLI.              | [dr-cli installation guide](https://github.com/datarobot-oss/cli?tab=readme-ov-file#installation) |
| **git**      | >= 2.30.0  | A version control system.       | [git installation guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) |
| **uv**       | >= 0.6.10  | A Python package manager.       | [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)     |
| **Pulumi**   | >= 3.163.0 | An Infrastructure as Code tool. | [Pulumi installation guide](https://www.pulumi.com/docs/iac/download-install/)        |
| **Taskfile** | >= 3.43.3  | A task runner.                  | [Taskfile installation guide](https://taskfile.dev/docs/installation)                 |
| **NodeJS**   | >= 24      | JavaScript runtime for frontend development. | [NodeJS installation guide](https://nodejs.org/en/download/)                |

> **IMPORTANT**: You will also need a compatible C++ compiler and build tools installed on your system to compile some Python packages.

### Development Container (experimental)

[devcontainers](https://containers.dev/) allows using a container environment for local development experience. It is integrated with
[modern IDEs, such as VSCode and PyCharm](https://containers.dev/supporting), and [Dev Container CLI](https://containers.dev/supporting#devcontainer-cli) allows you to integrate it with Terminal-centric development experience.

> This can also be used as a solution for Windows development.

```diff
-[Docker Desktop](https://docs.docker.com/desktop/) is the recomended backend for running devcontainers, but any docker-compatible backend is supported.
```

This template offers a devcontainer with all pre-requisites installed. To start working in it, simply open the template in PyCharm (version >= 2023.2, Pro) or VSCode, and IDE will prompt you to re-open in a container:

![Open in Dev Container PyCharm](docs/img/pycharm-devcontainer.png)

![Open in Dev Container VSCode](docs/img/vscode-devcontainer.png)


If you work directly in the terminal, do:

```shell
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . /bin/sh
```

## Prepare application

As the last step, do `task start` to prepare you local development environment. An interactive wizard will guide you though selection of
configuration options

<details>

<summary>☂️ Configuration options explained</summary>

## LLM configuration

Agentic Application supports multiple flexible LLM options including:

- LLM Blueprint with LLM Gateway (default)
- LLM Blueprint with an External LLM
- Already Deployed Text Generation model in DataRobot

### LLM Configuration Recommended Option

You can edit the LLM configuration by manually changing which configuration is active.
Simply run:

```sh
ln -sf ../configurations/<chosen_configuration> infra/infra/llm.py
```

After doing so, you'll likely want to edit the llm.py to have the correct model selected. Particularly
for non-LLM Gateway options.

### LLM Configuration Alternative Option

If you want to do it dynamically, you can set it as a configuration value with:

```sh
INFRA_ENABLE_LLM=<chosen_configuration>
```

from the list of options in the `infra/configurations/llm` folder.

Here are some examples of each configuration using the dynamic option described above:

#### LLM Blueprint with LLM Gateway (default)

Default option is LLM Gateway if not specified in your `.env` file.

```sh
INFRA_ENABLE_LLM=blueprint_with_llm_gateway.py
```

#### Existing LLM Deployment in DataRobot

Uncomment and configure these in your `.env` file:

```sh
TEXTGEN_DEPLOYMENT_ID=<your_deployment_id>
INFRA_ENABLE_LLM=deployed_llm.py
```

#### External LLM Provider

Configure an LLM with an external LLM provider like Azure, Bedrock, Anthropic, or VertexAI. Here's an Azure AI example:

```sh
INFRA_ENABLE_LLM=blueprint_with_external_llm.py
LLM_DEFAULT_MODEL="azure/gpt-4o"
OPENAI_API_VERSION='2024-08-01-preview'
OPENAI_API_BASE='https://<your_custom_endpoint>.openai.azure.com'
OPENAI_API_DEPLOYMENT_ID='<your deployment_id>'
OPENAI_API_KEY='<your_api_key>'
```

See the [DataRobot documentation](https://docs.datarobot.com/en/docs/gen-ai/playground-tools/deploy-llm.html) for details on other providers.

In addition to the changes for the `.env` file, you can also edit the respective llm.py file to make additional changes
such as the default LLM, temperature, top_p, etc within the chosen configuration


## OAuth Applications

The template can work with files stored in Google Drive and Box.
In order to give it access to those files, you need to configure OAuth Applications.

### Google OAuth Application

- Go to [Google API Console](https://console.developers.google.com/) from your Google account
- Navigate to "APIs & Services" > "Enabled APIs & services" > "Enable APIs and services" search for Drive, and add it.
- Navigate to "APIs & Services" > "OAuth consent screen" and make sure you have your consent screen configured. You may have both "External" and "Internal" audience types.
- Navigate to "APIs & Services" > "Credentials" and click on the "Create Credentials" button. Select "OAuth client ID".
- Select "Web application" as Application type, fill in "Name" & "Authorized redirect URIs" fields. For example, for local development, the redirect URL will be:
  - `http://localhost:5173/oauth/callback` - local vite dev server (used by frontend folks)
  - `http://localhost:8080/oauth/callback` - web-proxied frontend
  - `http://localhost:8080/api/v1/oauth/callback/` - the local web API (optional).
  - For production, you'll want to add your DataRobot callback URL. For example, in US Prod it is `https://app.datarobot.com/custom_applications/{appId}/oauth/callback`. For any installation of DataRobot it is `https://<datarobot-endpoint>/custom_applications/{appId}/oauth/callback`.
- Hit the "Create" button when you are done.
- Copy the "Client ID" and "Client Secret" values from the created OAuth client ID and set them in the template env variables as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` correspondingly.
- Make sure you have the "Google Drive API" enabled in the "APIs & Services" > "Library" section. Otherwise, you will get 403 errors.
- Finally, go to "APIs & Services" > "OAuth consent screen" > "Data Access" and make sure you have the following scopes selected:
  - `openid`
  - `https://www.googleapis.com/auth/userinfo.email`
  - `https://www.googleapis.com/auth/userinfo.profile`
  - `https://www.googleapis.com/auth/drive.readonly`

### Box OAuth Application

- Head to [Box Developer Console](https://app.box.com/developers/console) from your Box account
- Create a new platform application, then select "Custom App" type
- Fill in "Application Name" and select "Purpose" (e.g. "Integration"). Then, fill in three more info fields. The actual selection doesn't matter.
- Select "User Authentication (OAuth 2.0)" as Authentication Method and click on the "Create App" button
- In the "OAuth 2.0 Redirect URIs" section, please fill in callback URLs you want to use.
  - `http://localhost:5173/oauth/callback` - local vite dev server (used by frontend folks)
  - `http://localhost:8080/oauth/callback` - web-proxied frontend
  - `http://localhost:8080/api/v1/oauth/callback/` - the local web API (optional).
  - For production, you'll want to add your DataRobot callback URL. For example, in US Prod it is `https://app.datarobot.com/custom_applications/{appId}/oauth/callback`.
- Hit "Save Changes" after that.
- Under the "Application Scopes", please make sure you have both `Read all files and folders stored in Box` and "Write all files and folders store in Box" checkboxes selected. We need both because we need to "write" to the log that we've downloaded the selected files.
- Finally, under the "OAuth 2.0 Credentials" section, you should be able to find your Client ID and Client Secret pair to setup in the template env variables as `BOX_CLIENT_ID` and `BOX_CLIENT_SECRET` correspondingly.

After you've set those in your project `.env` file, on the next Pulumi Up, we'll create OAuth
providers in your DataRobot installation. To view and manage those and verify they are working
navigate to `<your_datarobot_url>/account/oauth-providers` or in US production: https://app.datarobot.com/account/oauth-providers.

Additionally, the Pulumi output variables get used to populate those providers for your Codespace and
local development environment as well.

</details>


# Run your agent

## Option 1: autoreload for backend, static frontend

Build the frontend:
```shell
task frontend_web:build
```

Start the application:

```shell
task web:dev
```

Start the writer agent:

```shell
task writer_agent:dev
```

And go to http://localhost:8080.

## Option 2: autoreload for all components

Instead of `task frontend_web:build` do `task frontend_web:dev`, and go to http://localhost:5173/

## Option 3 (experimental): just agent playground

If you want to test just the agent without application you can do:

```shell

task writer_agent:dev
```

then:
```shell
task writer_agent:chainlit
```

This will start a separate frontend application just for your local agent at http://localhost:8083/.

# Develop your agent

Once setup is complete, you are ready customize your agent, allowing you to add your own logic and functionality to the agent.
See the following documentation for more details:

- [Customize your agent](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-development.html)
- [Add tools to your agent](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-tools-integrate.html)
- [Configure LLM providers](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-llm-providers.html)
- [Use the agent CLI](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-cli-guide.html)
- [Add Python requirements](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-python-packages.html)

# Deploy your agent

After you tested your agent locally, just run

```shell
task deploy
```

to deploy it to DataRobot.

# Get help

If you encounter issues or have questions, try the following:

- [Contact DataRobot](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html) for support.
- Open an issue on the [GitHub repository](https://github.com/datarobot-community/datarobot-agent-application).
