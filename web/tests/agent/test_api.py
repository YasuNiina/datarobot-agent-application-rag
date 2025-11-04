# Copyright 2025 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from typing import AsyncGenerator

import pytest
from ag_ui.core import (
    BaseEvent,
    EventType,
    RunAgentInput,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    UserMessage,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agent.api import add_agui_agent_fastapi_endpoint
from app.agent.base import AGUIAgent


# Create a mock AGUIAgent for testing
class MockAGUIAgent(AGUIAgent):
    """Mock agent for testing."""

    def __init__(self, name: str = "test_agent", events: list[BaseEvent] | None = None):
        super().__init__(name)
        self.events = events or []

    async def run(self, input: RunAgentInput) -> AsyncGenerator[BaseEvent, None]:
        """Mock run method that yields predefined events."""
        for event in self.events:
            yield event


@pytest.fixture
def mock_agent() -> AGUIAgent:
    """Create a mock agent with sample events."""
    events = [
        TextMessageStartEvent(message_id="1", role="assistant"),
        TextMessageContentEvent(message_id="1", delta="Hello world!"),
        TextMessageEndEvent(message_id="1"),
    ]
    return MockAGUIAgent(name="test_agent", events=events)


@pytest.fixture
def mock_run_agent_input() -> RunAgentInput:
    """Create a mock run agent input."""
    return RunAgentInput(
        thread_id="1",
        run_id="1",
        state={},
        messages=[
            UserMessage(id="1", role="user", content="Hello world!"),
        ],
        tools=[],
        context=[],
        forwarded_props={},
    )


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI app for testing."""
    return FastAPI()


def test_add_agui_agent_fastapi_endpoint_creates_endpoints(
    app: FastAPI, mock_agent: AGUIAgent, mock_run_agent_input: RunAgentInput
) -> None:
    """Test that the function adds both POST and health endpoints to FastAPI app."""
    # Add the agent endpoint
    add_agui_agent_fastapi_endpoint(app, mock_agent, path="/agent")

    # Create test client
    client = TestClient(app)

    # Test that the POST endpoint exists
    with client.stream(
        "POST", "/agent", json=mock_run_agent_input.model_dump()
    ) as response:
        events = []
        for event in response.iter_lines():
            if not event.startswith("data: "):
                continue
            event_str = event.split("data: ")[1]
            event_obj = json.loads(event_str)
            events.append(event_obj)
        assert len(events) == 3
        assert events[0]["type"] == EventType.TEXT_MESSAGE_START
        assert events[1]["type"] == EventType.TEXT_MESSAGE_CONTENT
        assert events[2]["type"] == EventType.TEXT_MESSAGE_END

    # Test that the health endpoint exists
    response = client.get("/agent/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "agent": {"name": "test_agent"}}


def test_add_agui_agent_fastapi_endpoint_default_path(
    app: FastAPI, mock_agent: AGUIAgent, mock_run_agent_input: RunAgentInput
) -> None:
    """Test that the function uses default path '/' when not specified."""
    # Add the agent endpoint with default path
    add_agui_agent_fastapi_endpoint(app, mock_agent)

    # Create test client
    client = TestClient(app)

    # Test that the POST endpoint exists at root
    response = client.post("/", json=mock_run_agent_input.model_dump())
    assert response.status_code == 200

    # Test that the health endpoint exists at /health
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["agent"]["name"] == "test_agent"


def test_health_endpoint_returns_correct_agent_name(app: FastAPI) -> None:
    """Test that health endpoint returns the correct agent name."""
    # Create agents with different names
    agent1 = MockAGUIAgent(name="agent_one")
    agent2 = MockAGUIAgent(name="agent_two")

    # Add both agents at different paths
    add_agui_agent_fastapi_endpoint(app, agent1, path="/agent1")
    add_agui_agent_fastapi_endpoint(app, agent2, path="/agent2")

    # Create test client
    client = TestClient(app)

    # Test health endpoints
    response1 = client.get("/agent1/health")
    assert response1.json()["agent"]["name"] == "agent_one"

    response2 = client.get("/agent2/health")
    assert response2.json()["agent"]["name"] == "agent_two"


def test_agent_endpoint_error_handling(
    app: FastAPI, mock_run_agent_input: RunAgentInput
) -> None:
    """Test that the endpoint handles agent errors gracefully."""

    class ErrorAgent(AGUIAgent):
        """Agent that raises an error."""

        async def run(self, input: RunAgentInput) -> AsyncGenerator[BaseEvent, None]:
            raise ValueError("Test error")
            yield  # This is never reached but needed for the async generator type

    error_agent = ErrorAgent(name="error_agent")

    # Add the agent endpoint
    add_agui_agent_fastapi_endpoint(app, error_agent, path="/agent")

    # Create test client
    client = TestClient(app)

    # Make a POST request - should raise the error
    with pytest.raises(ValueError, match="Test error"):
        client.post("/agent", json=mock_run_agent_input.model_dump())


def test_path_with_trailing_slash(
    app: FastAPI, mock_agent: AGUIAgent, mock_run_agent_input: RunAgentInput
) -> None:
    """Test that paths with trailing slashes work correctly."""
    # Add the agent endpoint with trailing slash
    add_agui_agent_fastapi_endpoint(app, mock_agent, path="/agent/")

    # Create test client
    client = TestClient(app)

    # Both with and without trailing slash should work (FastAPI normalizes this)
    response = client.post("/agent/", json=mock_run_agent_input.model_dump())
    assert response.status_code == 200

    response = client.get("/agent/health/")
    assert response.status_code == 200
