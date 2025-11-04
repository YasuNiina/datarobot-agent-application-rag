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

import os
from collections.abc import AsyncGenerator
from typing import Any

from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import StreamingResponse

from app.agent.base import AGUIAgent


def add_agui_agent_fastapi_endpoint(
    app: FastAPI | APIRouter, agent: AGUIAgent, path: str = "/"
) -> None:
    """Adds an endpoint to the FastAPI app."""

    @app.post(path)
    async def agent_endpoint(
        input_data: RunAgentInput, request: Request
    ) -> StreamingResponse:
        # Get the accept header from the request
        accept_header = request.headers.get("accept") or ""

        # Create an event encoder to properly format SSE events
        encoder = EventEncoder(accept=accept_header)

        async def event_generator() -> AsyncGenerator[str, None]:
            async for event in agent.run(input_data):
                yield encoder.encode(event)

        return StreamingResponse(
            event_generator(), media_type=encoder.get_content_type()
        )

    @app.get(os.path.join(path, "health"))
    def health() -> dict[str, Any]:
        """Health check."""
        return {
            "status": "ok",
            "agent": {
                "name": agent.name,
            },
        }
