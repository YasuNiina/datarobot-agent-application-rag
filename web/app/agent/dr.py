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

import logging
import uuid
from typing import Any, AsyncGenerator, Dict

from ag_ui.core import (
    BaseEvent,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk

from app.agent.base import AGUIAgent

logger = logging.getLogger(__name__)


class DataRobotAGUIAgent(AGUIAgent):
    """AG-UI wrapper for a DataRobot Agent."""

    def __init__(self, name: str, url: str):
        super().__init__(name)
        self.url = url
        self.client = AsyncOpenAI(base_url=url, api_key="empty")

    async def run(self, input: RunAgentInput) -> AsyncGenerator[BaseEvent, None]:
        async for event_str in self._handle_stream_events(input):
            yield event_str

    async def _handle_stream_events(
        self, input: RunAgentInput
    ) -> AsyncGenerator[BaseEvent, None]:
        yield RunStartedEvent(thread_id=input.thread_id, run_id=input.run_id)
        try:
            message_id = str(uuid.uuid4())

            yield TextMessageStartEvent(message_id=message_id, role="assistant")

            generator: AsyncStream[
                ChatCompletionChunk
            ] = await self.client.chat.completions.create(
                **self._prepare_chat_completions_input(input)
            )
            async for chunk in generator:
                if chunk.choices[0].delta and chunk.choices[0].delta.content:
                    # TODO: tool calling events
                    yield TextMessageContentEvent(
                        message_id=message_id, delta=chunk.choices[0].delta.content
                    )
            yield TextMessageEndEvent(message_id=message_id)

            yield RunFinishedEvent(thread_id=input.thread_id, run_id=input.run_id)

        except Exception as e:
            logger.exception("Error during agent run")
            yield RunErrorEvent(message=str(e))

    def _prepare_chat_completions_input(self, input: RunAgentInput) -> Dict[str, Any]:
        messages = []
        for input_message in input.messages:
            messages.append(
                {
                    "role": input_message.role,
                    "content": input_message.content,
                }
            )
        return {
            "messages": messages,
            "model": "datarobot/azure/gpt-4o-mini",
            "stream": True,
        }
