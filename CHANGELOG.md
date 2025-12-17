# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## 11.4.4
- Fix not publishing fastapi_server/static directory

## 11.4.3
- Fix devcontainers configuration

## 11.4.2
- Rename custom_model to agentic_workflow
- Rename web to fastapi_server
- Fix tracing when using threading
- Display tool invocations and results on the UI
- Implement background chats
- Fix mapping for chat history endpoint

## 11.4.0
- Reduce agents to just planner and writer
- Fix the default model used everywhere to be a non-deprecated model
- Fix issues related to docker_context usage in infra and move logic to fixed pulumi for version pinning
- Fix NAT streaming
- Event streaming for langgraph
- Add parameter DATABASE_URI to setup wizard
- Fix devcontainer configuration
- Fix execution environment pinning in edge case with blank version id
- Fix CVEs
- Remove temperature from NAT workflow.yaml

## 11.3.4
- Add versions file

## 11.3.3
- Fix the root Taskfile

## 11.3.2
- Improvements to dev containers and start experience

## 11.3.1
- Fix error handling in UI
- Remove mastra dependencies
- Full dr start experience
- Fix autoscroll behavior
- OAuth fixes

## 11.3.0
- Fix devcontainer not compiling Dockerfile
- Restore missing chainlit lit.py
- Pin pulumi version so that it doesn't encounter github rate limiting
- Show an error message in case agent response is empty
- Fix migrations in task start

## 0.0.6

## 0.0.5

## 0.0.4

## 0.0.3

## 0.0.2

## 0.0.1
- Auto-select (and create) pulumi stack if env variable is present
- Upgrade datarobot in pyproject.toml
- Append pulumi stack name from environment if present to all pulumi commands
- Simplify all pulumi local and remote naming
- Initial implementation
