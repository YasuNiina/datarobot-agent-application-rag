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

"""DataRobot RAG tool for querying a RAG deployment via OpenAI-compatible Chat API."""

import json
import logging
import os

from openai import OpenAI

from datarobot_genai.drmcp import dr_mcp_tool

logger = logging.getLogger(__name__)

# Configuration from environment variables
DR_RAG_DEPLOYMENT_ID = os.environ.get("DR_RAG_DEPLOYMENT_ID")
DR_RAG_ENDPOINT = os.environ.get(
    "DR_RAG_ENDPOINT", os.environ.get("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
)
DR_RAG_API_TOKEN = os.environ.get(
    "DR_RAG_API_TOKEN", os.environ.get("DATAROBOT_API_TOKEN", "")
)

# Only register as MCP tools when the RAG deployment is configured.
# When not configured, functions remain defined (for testing) but are not
# exposed through the MCP server.
if not DR_RAG_DEPLOYMENT_ID:
    logger.info(
        "DR_RAG_DEPLOYMENT_ID is not set; RAG query tools will not be registered."
    )
_register_tool = dr_mcp_tool() if DR_RAG_DEPLOYMENT_ID else (lambda f: f)

# Model name constant for DataRobot's OpenAI-compatible endpoint
DEFAULT_CHAT_MODEL_NAME = "datarobot-deployed-llm"


def _get_openai_client() -> OpenAI:
    """Return an OpenAI client configured for the DataRobot Chat API endpoint."""
    base_url = f"{DR_RAG_ENDPOINT}/deployments/{DR_RAG_DEPLOYMENT_ID}"
    return OpenAI(base_url=base_url, api_key=DR_RAG_API_TOKEN)


def _format_citations(citations: list[dict[str, object]]) -> str:
    """Format citation data from the DataRobot response into readable text.

    Args:
        citations: List of citation dicts with 'content' and 'metadata' keys.

    Returns:
        Formatted citation string, or empty string if no citations.
    """
    if not citations:
        return ""

    parts: list[str] = ["\n\n---\n**References:**"]
    for i, cite in enumerate(citations, 1):
        metadata = cite.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        source = metadata.get("source", "Unknown")
        page = metadata.get("page", "")
        content = str(cite.get("content", ""))[:200]

        header = f"\n[{i}] {source}"
        if page:
            header += f" (p.{page})"
        parts.append(header)
        if content:
            parts.append(f"    {content}...")

    return "\n".join(parts)


@_register_tool
async def query_datarobot_rag(question: str) -> str:
    """Query the DataRobot RAG deployment and get an answer with citations.

    Use this tool when you need to search internal documents or knowledge bases
    to answer a user's question. The tool sends the question to DataRobot's
    RAG pipeline which searches a vector database for relevant documents and
    generates an answer using an LLM.

    Args:
        question: The question text to ask the RAG system.

    Returns:
        The answer text with citation references appended.
    """
    if not DR_RAG_DEPLOYMENT_ID:
        return "Error: DR_RAG_DEPLOYMENT_ID is not configured."

    client = _get_openai_client()

    messages: list[dict[str, str]] = []

    system_prompt = os.environ.get("DR_RAG_SYSTEM_PROMPT")
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": question})

    logger.info(
        "Sending query to DataRobot RAG deployment %s", DR_RAG_DEPLOYMENT_ID
    )

    completion = client.chat.completions.create(
        model=DEFAULT_CHAT_MODEL_NAME,
        messages=messages,  # type: ignore[arg-type]
        stream=False,
    )

    content = completion.choices[0].message.content or ""

    # Extract citations from DataRobot-specific extension fields
    citations: list[dict[str, object]] = []
    if hasattr(completion, "model_extra") and completion.model_extra:
        citations = completion.model_extra.get("citations", [])

    citation_text = _format_citations(citations)

    return content + citation_text


@_register_tool
async def query_datarobot_rag_with_context(
    question: str,
    conversation_history: str = "",
) -> str:
    """Query the DataRobot RAG deployment with conversation context.

    Use this tool when you need to ask a follow-up question that depends on
    previous conversation context. Pass the conversation history as a JSON
    string containing an array of message objects with 'role' and 'content'.

    Args:
        question: The current question text.
        conversation_history: Previous conversation as a JSON string
            (e.g., '[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]').

    Returns:
        The answer text with citation references appended.
    """
    if not DR_RAG_DEPLOYMENT_ID:
        return "Error: DR_RAG_DEPLOYMENT_ID is not configured."

    client = _get_openai_client()

    messages: list[dict[str, str]] = []

    system_prompt = os.environ.get("DR_RAG_SYSTEM_PROMPT")
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Restore conversation history
    if conversation_history:
        try:
            history = json.loads(conversation_history)
            if isinstance(history, list):
                for msg in history:
                    if isinstance(msg, dict):
                        messages.append(
                            {
                                "role": msg.get("role", "user"),
                                "content": msg.get("content", ""),
                            }
                        )
        except json.JSONDecodeError:
            logger.warning("Failed to parse conversation_history JSON")

    messages.append({"role": "user", "content": question})

    logger.info(
        "Sending contextual query to DataRobot RAG deployment %s "
        "with %d history messages",
        DR_RAG_DEPLOYMENT_ID,
        len(messages) - 1,
    )

    completion = client.chat.completions.create(
        model=DEFAULT_CHAT_MODEL_NAME,
        messages=messages,  # type: ignore[arg-type]
        stream=False,
    )

    content = completion.choices[0].message.content or ""

    citations: list[dict[str, object]] = []
    if hasattr(completion, "model_extra") and completion.model_extra:
        citations = completion.model_extra.get("citations", [])

    return content + _format_citations(citations)
