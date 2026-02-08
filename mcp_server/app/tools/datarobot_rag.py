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

"""DataRobot RAG tool with advanced pipeline: query optimization, chunk filtering, and answer generation."""

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

# Optional: LLM deployment for query optimization and chunk filtering.
# When set, enables the advanced RAG pipeline.
# Must point to a text generation LLM deployment (NOT the RAG deployment).
DR_LLM_DEPLOYMENT_ID = os.environ.get("DR_LLM_DEPLOYMENT_ID")

# Only register as MCP tools when the RAG deployment is configured.
# When not configured, functions remain defined (for testing) but are not
# exposed through the MCP server.
if not DR_RAG_DEPLOYMENT_ID:
    logger.info(
        "DR_RAG_DEPLOYMENT_ID is not set; RAG query tools will not be registered."
    )
if DR_LLM_DEPLOYMENT_ID:
    logger.info(
        "DR_LLM_DEPLOYMENT_ID is set; advanced RAG pipeline (query optimization, "
        "chunk filtering, answer generation) is enabled."
    )
else:
    logger.info(
        "DR_LLM_DEPLOYMENT_ID is not set; using simple RAG pipeline."
    )
_register_tool = dr_mcp_tool() if DR_RAG_DEPLOYMENT_ID else (lambda f: f)

# Model name constant for DataRobot's OpenAI-compatible endpoint
DEFAULT_CHAT_MODEL_NAME = "datarobot-deployed-llm"


def _get_openai_client() -> OpenAI:
    """Return an OpenAI client configured for the DataRobot RAG Chat API endpoint."""
    base_url = f"{DR_RAG_ENDPOINT}/deployments/{DR_RAG_DEPLOYMENT_ID}"
    return OpenAI(base_url=base_url, api_key=DR_RAG_API_TOKEN)


def _get_llm_client() -> OpenAI:
    """Return an OpenAI client configured for the LLM deployment (query optimization, etc.)."""
    base_url = f"{DR_RAG_ENDPOINT}/deployments/{DR_LLM_DEPLOYMENT_ID}"
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


# ---------------------------------------------------------------------------
# Advanced RAG pipeline helpers
# ---------------------------------------------------------------------------

_QUERY_OPTIMIZATION_SYSTEM_PROMPT = (
    "You are a query optimization specialist. Your task is to transform the user's "
    "question into an optimized search query for vector database retrieval.\n"
    "Rules:\n"
    "- Remove filler words, greetings, and unnecessary context\n"
    "- Extract key concepts, entities, and technical terms\n"
    "- Include synonyms or related terms that might appear in documents\n"
    "- If the question is a follow-up, resolve references using conversation context "
    "(e.g., replace pronouns like 'it', 'that' with the actual subject)\n"
    "- Keep the query concise but comprehensive\n"
    "- Output ONLY the optimized query text, nothing else\n"
    "- Maintain the language of the original question"
)

_CHUNK_FILTER_SYSTEM_PROMPT = (
    "You are a relevance evaluator. Given a user's question and a list of text chunks "
    "retrieved from a knowledge base, determine which chunks contain information that is "
    "relevant and useful for answering the question.\n"
    "Output ONLY a JSON array of the relevant chunk indices (0-based).\n"
    "Example output: [0, 2, 3]\n"
    "If no chunks are relevant, output: []"
)

_ANSWER_GENERATION_SYSTEM_PROMPT = (
    "You are a knowledgeable assistant. Answer the user's question based strictly on the "
    "provided context chunks retrieved from a knowledge base.\n"
    "Rules:\n"
    "- Only use information from the provided context\n"
    "- Include numbered citation references (e.g., [1], [2]) corresponding to the chunk "
    "numbers when you use information from a specific chunk\n"
    "- If the context doesn't contain enough information, honestly say so\n"
    "- Answer in the same language as the user's question\n"
    "- Be comprehensive but concise"
)


def _optimize_query(
    question: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """Use LLM to transform the user's question into an optimized vector search query.

    Args:
        question: The original user question.
        conversation_history: Optional prior conversation messages for context.

    Returns:
        The optimized search query string.
    """
    client = _get_llm_client()
    messages: list[dict[str, str]] = [
        {"role": "system", "content": _QUERY_OPTIMIZATION_SYSTEM_PROMPT},
    ]

    if conversation_history:
        context_lines = []
        for msg in conversation_history[-4:]:
            context_lines.append(f"{msg['role']}: {msg['content']}")
        context_block = "\n".join(context_lines)
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Recent conversation:\n{context_block}\n\n"
                    f"Current question: {question}\n\n"
                    "Optimized search query:"
                ),
            }
        )
    else:
        messages.append(
            {
                "role": "user",
                "content": f"Question: {question}\n\nOptimized search query:",
            }
        )

    completion = client.chat.completions.create(
        model=DEFAULT_CHAT_MODEL_NAME,
        messages=messages,  # type: ignore[arg-type]
        stream=False,
    )
    optimized = (completion.choices[0].message.content or "").strip()
    return optimized if optimized else question


def _filter_chunks(
    question: str,
    chunks: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Use LLM to evaluate and filter chunks for relevance to the question.

    Args:
        question: The original user question.
        chunks: List of citation/chunk dicts from the RAG response.

    Returns:
        Filtered list containing only relevant chunks.
    """
    if not chunks:
        return []

    client = _get_llm_client()

    chunk_descriptions = []
    for i, chunk in enumerate(chunks):
        content = str(chunk.get("content", ""))
        chunk_descriptions.append(f"[Chunk {i}]: {content}")
    chunks_text = "\n\n".join(chunk_descriptions)

    completion = client.chat.completions.create(
        model=DEFAULT_CHAT_MODEL_NAME,
        messages=[
            {"role": "system", "content": _CHUNK_FILTER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Chunks:\n{chunks_text}\n\n"
                    "Relevant chunk indices:"
                ),
            },
        ],  # type: ignore[arg-type]
        stream=False,
    )

    response = (completion.choices[0].message.content or "").strip()

    try:
        indices = json.loads(response)
        if isinstance(indices, list):
            return [
                chunks[i]
                for i in indices
                if isinstance(i, int) and 0 <= i < len(chunks)
            ]
    except (json.JSONDecodeError, IndexError):
        logger.warning(
            "Failed to parse chunk filter response: %s — returning all chunks",
            response[:200],
        )

    return chunks


def _generate_answer(
    question: str,
    chunks: list[dict[str, object]],
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """Use LLM to generate a final answer from filtered chunks.

    Args:
        question: The original user question.
        chunks: Filtered relevant chunks.
        conversation_history: Optional prior conversation for context.

    Returns:
        Generated answer text.
    """
    client = _get_llm_client()

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        source = metadata.get("source", "Unknown")
        page = metadata.get("page", "")
        content = str(chunk.get("content", ""))

        ref = f"[{i}] Source: {source}"
        if page:
            ref += f", p.{page}"
        context_parts.append(f"{ref}\n{content}")
    context_text = "\n\n---\n\n".join(context_parts)

    custom_system_prompt = os.environ.get("DR_RAG_SYSTEM_PROMPT", "")
    system_content = _ANSWER_GENERATION_SYSTEM_PROMPT
    if custom_system_prompt:
        system_content = f"{custom_system_prompt}\n\n{system_content}"

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_content},
    ]

    if conversation_history:
        for msg in conversation_history:
            messages.append(msg)

    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context_text}\n\nQuestion: {question}",
        }
    )

    completion = client.chat.completions.create(
        model=DEFAULT_CHAT_MODEL_NAME,
        messages=messages,  # type: ignore[arg-type]
        stream=False,
    )
    return completion.choices[0].message.content or ""


def _advanced_rag_pipeline(
    question: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """Execute the advanced RAG pipeline.

    Steps:
        1. Optimize the user's query for vector database search.
        2. Retrieve chunks via the RAG deployment using the optimized query.
        3. Filter retrieved chunks for relevance to the original question.
        4. Generate a final answer from the filtered chunks.

    Falls back to the RAG deployment's raw answer if any step fails.

    Args:
        question: The original user question.
        conversation_history: Optional prior conversation messages.

    Returns:
        The final answer with citation references.
    """
    # -- Step 1: Optimize query --
    try:
        optimized_query = _optimize_query(question, conversation_history)
        logger.info(
            "Query optimized: '%s' -> '%s'",
            question[:80],
            optimized_query[:80],
        )
    except Exception:
        logger.warning("Query optimization failed, using original question", exc_info=True)
        optimized_query = question

    # -- Step 2: Retrieve via RAG deployment --
    rag_client = _get_openai_client()
    rag_messages: list[dict[str, str]] = []

    system_prompt = os.environ.get("DR_RAG_SYSTEM_PROMPT")
    if system_prompt:
        rag_messages.append({"role": "system", "content": system_prompt})

    rag_messages.append({"role": "user", "content": optimized_query})

    logger.info(
        "Sending optimized query to DataRobot RAG deployment %s",
        DR_RAG_DEPLOYMENT_ID,
    )

    completion = rag_client.chat.completions.create(
        model=DEFAULT_CHAT_MODEL_NAME,
        messages=rag_messages,  # type: ignore[arg-type]
        stream=False,
    )

    fallback_answer = completion.choices[0].message.content or ""

    # Extract citations (chunks) from the response
    citations: list[dict[str, object]] = []
    if hasattr(completion, "model_extra") and completion.model_extra:
        citations = completion.model_extra.get("citations", [])

    if not citations:
        logger.info("No citations returned; returning RAG deployment answer as-is")
        return fallback_answer

    # -- Step 3: Filter chunks for relevance --
    try:
        filtered_chunks = _filter_chunks(question, citations)
        logger.info(
            "Chunk filtering: %d -> %d chunks retained",
            len(citations),
            len(filtered_chunks),
        )
    except Exception:
        logger.warning("Chunk filtering failed, using all chunks", exc_info=True)
        filtered_chunks = citations

    if not filtered_chunks:
        return fallback_answer + _format_citations(citations)

    # -- Step 4: Generate answer from filtered chunks --
    try:
        answer = _generate_answer(question, filtered_chunks, conversation_history)
        logger.info("Answer generated from %d filtered chunks", len(filtered_chunks))
    except Exception:
        logger.warning(
            "Answer generation failed, falling back to RAG deployment answer",
            exc_info=True,
        )
        return fallback_answer + _format_citations(filtered_chunks)

    return answer + _format_citations(filtered_chunks)


# ---------------------------------------------------------------------------
# MCP tool functions
# ---------------------------------------------------------------------------


@_register_tool
async def query_datarobot_rag(question: str) -> str:
    """Query the DataRobot RAG deployment and get an answer with citations.

    Use this tool when you need to search internal documents or knowledge bases
    to answer a user's question. The tool sends the question to DataRobot's
    RAG pipeline which searches a vector database for relevant documents and
    generates an answer using an LLM.

    When advanced mode is enabled (DR_LLM_DEPLOYMENT_ID is configured), the tool
    automatically optimizes the search query, filters retrieved chunks for
    relevance, and generates a higher-quality answer.

    Args:
        question: The question text to ask the RAG system.

    Returns:
        The answer text with citation references appended.
    """
    if not DR_RAG_DEPLOYMENT_ID:
        return "Error: DR_RAG_DEPLOYMENT_ID is not configured."

    # Use advanced pipeline when LLM deployment is available
    if DR_LLM_DEPLOYMENT_ID:
        return _advanced_rag_pipeline(question)

    # Fallback: simple pipeline
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

    When advanced mode is enabled (DR_LLM_DEPLOYMENT_ID is configured), the tool
    automatically optimizes the search query (resolving references from context),
    filters retrieved chunks for relevance, and generates a higher-quality answer.

    Args:
        question: The current question text.
        conversation_history: Previous conversation as a JSON string
            (e.g., '[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]').

    Returns:
        The answer text with citation references appended.
    """
    if not DR_RAG_DEPLOYMENT_ID:
        return "Error: DR_RAG_DEPLOYMENT_ID is not configured."

    # Parse conversation history
    parsed_history: list[dict[str, str]] = []
    if conversation_history:
        try:
            history = json.loads(conversation_history)
            if isinstance(history, list):
                for msg in history:
                    if isinstance(msg, dict):
                        parsed_history.append(
                            {
                                "role": msg.get("role", "user"),
                                "content": msg.get("content", ""),
                            }
                        )
        except json.JSONDecodeError:
            logger.warning("Failed to parse conversation_history JSON")

    # Use advanced pipeline when LLM deployment is available
    if DR_LLM_DEPLOYMENT_ID:
        return _advanced_rag_pipeline(
            question,
            conversation_history=parsed_history if parsed_history else None,
        )

    # Fallback: simple pipeline
    client = _get_openai_client()

    messages: list[dict[str, str]] = []

    system_prompt = os.environ.get("DR_RAG_SYSTEM_PROMPT")
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.extend(parsed_history)
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
