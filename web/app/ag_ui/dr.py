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
    ToolCallChunkEvent,
)
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk

from app.ag_ui.base import AGUIAgent
from app.config import Config

logger = logging.getLogger(__name__)


class DataRobotAGUIAgent(AGUIAgent):
    """AG-UI wrapper for a DataRobot Agent."""

    def __init__(self, name: str, config: Config):
        super().__init__(name)
        self.url = config.writer_agent_endpoint
        self.client = AsyncOpenAI(
            base_url=self.url,
            api_key=config.datarobot_api_token,
            default_headers={"Authorization": f"Bearer {config.datarobot_api_token}"},
        )

    async def run(self, input: RunAgentInput) -> AsyncGenerator[BaseEvent, None]:
        async for event_str in self._handle_stream_events(input):
            yield event_str

    async def _handle_stream_events(
        self, input: RunAgentInput
    ) -> AsyncGenerator[BaseEvent, None]:
        yield RunStartedEvent(thread_id=input.thread_id, run_id=input.run_id)
        try:
            message_id = str(uuid.uuid4())

            yield TextMessageStartEvent(message_id=message_id)

            logger.debug("Sending request to agent's chat completion endpoint")

            generator: AsyncStream[
                ChatCompletionChunk
            ] = await self.client.chat.completions.create(
                **self._prepare_chat_completions_input(input)
            )
            async for chunk in generator:
                if not chunk.choices:
                    continue
                if len(chunk.choices) > 1:
                    logger.warning("Received more than one choice from chat completion")

                choice = chunk.choices[0]
                if choice.delta.content:
                    yield TextMessageContentEvent(
                        message_id=message_id, delta=choice.delta.content
                    )
                if choice.delta.tool_calls:
                    for tool_call in choice.delta.tool_calls:
                        yield ToolCallChunkEvent(
                            tool_call_id=tool_call.id,
                            tool_call_name=tool_call.function.name
                            if tool_call.function
                            else None,
                            delta=tool_call.function.arguments
                            if tool_call.function
                            else None,
                            parent_message_id=message_id,
                        )

            logger.debug("Processed all chat completions")

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
        # Agent does not currently use the `model` parameter,, butintreface requires it.
        return {
            "messages": messages,
            "model": "custom-model",
            "stream": True,
        }
