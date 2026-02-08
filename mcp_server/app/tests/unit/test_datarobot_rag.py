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
from unittest.mock import MagicMock, patch

import pytest

from app.tools.datarobot_rag import (
    _advanced_rag_pipeline,
    _filter_chunks,
    _format_citations,
    _generate_answer,
    _optimize_query,
    query_datarobot_rag,
    query_datarobot_rag_with_context,
)


class TestFormatCitations:
    """Tests for the _format_citations helper function."""

    def test_empty_citations(self) -> None:
        assert _format_citations([]) == ""

    def test_single_citation_with_source_and_page(self) -> None:
        citations = [
            {
                "content": "This is some citation content.",
                "metadata": {"source": "document.pdf", "page": "3"},
            }
        ]
        result = _format_citations(citations)
        assert "**References:**" in result
        assert "[1] document.pdf (p.3)" in result
        assert "This is some citation content." in result

    def test_single_citation_without_page(self) -> None:
        citations = [
            {
                "content": "Some content",
                "metadata": {"source": "readme.md"},
            }
        ]
        result = _format_citations(citations)
        assert "[1] readme.md" in result
        assert "(p." not in result

    def test_multiple_citations(self) -> None:
        citations = [
            {"content": "First", "metadata": {"source": "a.pdf", "page": "1"}},
            {"content": "Second", "metadata": {"source": "b.pdf", "page": "2"}},
        ]
        result = _format_citations(citations)
        assert "[1] a.pdf (p.1)" in result
        assert "[2] b.pdf (p.2)" in result

    def test_citation_with_empty_metadata(self) -> None:
        citations = [{"content": "text", "metadata": {}}]
        result = _format_citations(citations)
        assert "[1] Unknown" in result

    def test_citation_content_truncation(self) -> None:
        long_content = "x" * 300
        citations = [
            {"content": long_content, "metadata": {"source": "doc.pdf"}}
        ]
        result = _format_citations(citations)
        # Content should be truncated to 200 chars
        assert "x" * 200 + "..." in result
        assert "x" * 201 not in result


def _make_mock_completion(
    content: str, citations: list[dict[str, object]] | None = None
) -> MagicMock:
    """Build a mock ChatCompletion response."""
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = content
    if citations is not None:
        mock.model_extra = {"citations": citations}
    else:
        mock.model_extra = None
    return mock


# ---------------------------------------------------------------------------
# Simple pipeline tests (DR_LLM_DEPLOYMENT_ID not set)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestQueryDatarobotRag:
    """Tests for the query_datarobot_rag tool (simple pipeline)."""

    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", None)
    async def test_no_deployment_id(self) -> None:
        result = await query_datarobot_rag("test question")
        assert "Error" in result
        assert "DR_RAG_DEPLOYMENT_ID" in result

    @patch("app.tools.datarobot_rag.DR_LLM_DEPLOYMENT_ID", None)
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    @patch("app.tools.datarobot_rag._get_openai_client")
    async def test_basic_query(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("The answer is 42.")
        )

        result = await query_datarobot_rag("What is the answer?")

        assert "The answer is 42." in result
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert any(m["role"] == "user" and "What is the answer?" in m["content"] for m in messages)

    @patch("app.tools.datarobot_rag.DR_LLM_DEPLOYMENT_ID", None)
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    @patch("app.tools.datarobot_rag._get_openai_client")
    async def test_query_with_citations(self, mock_get_client: MagicMock) -> None:
        citations = [
            {
                "content": "Relevant passage",
                "metadata": {"source": "manual.pdf", "page": "5"},
            }
        ]
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("Answer text", citations)
        )

        result = await query_datarobot_rag("question")

        assert "Answer text" in result
        assert "manual.pdf" in result
        assert "p.5" in result

    @patch.dict(
        "os.environ", {"DR_RAG_SYSTEM_PROMPT": "You are a helpful assistant."}
    )
    @patch("app.tools.datarobot_rag.DR_LLM_DEPLOYMENT_ID", None)
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    @patch("app.tools.datarobot_rag._get_openai_client")
    async def test_system_prompt_included(
        self, mock_get_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("response")
        )

        await query_datarobot_rag("question")

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert messages[0]["role"] == "system"
        assert "helpful assistant" in messages[0]["content"]


@pytest.mark.asyncio
class TestQueryDatarobotRagWithContext:
    """Tests for the query_datarobot_rag_with_context tool (simple pipeline)."""

    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", None)
    async def test_no_deployment_id(self) -> None:
        result = await query_datarobot_rag_with_context("question")
        assert "Error" in result

    @patch("app.tools.datarobot_rag.DR_LLM_DEPLOYMENT_ID", None)
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    @patch("app.tools.datarobot_rag._get_openai_client")
    async def test_with_conversation_history(
        self, mock_get_client: MagicMock
    ) -> None:
        history = json.dumps(
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        )
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("Follow-up answer")
        )

        result = await query_datarobot_rag_with_context(
            "Follow-up question", history
        )

        assert "Follow-up answer" in result
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        # Should have history + current question
        assert len(messages) == 3
        assert messages[0]["content"] == "Hello"
        assert messages[1]["content"] == "Hi there!"
        assert messages[2]["content"] == "Follow-up question"

    @patch("app.tools.datarobot_rag.DR_LLM_DEPLOYMENT_ID", None)
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    @patch("app.tools.datarobot_rag._get_openai_client")
    async def test_with_invalid_history_json(
        self, mock_get_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("answer")
        )

        result = await query_datarobot_rag_with_context(
            "question", "not valid json"
        )

        assert "answer" in result
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        # Invalid history should be skipped, only the current question
        assert len(messages) == 1
        assert messages[0]["content"] == "question"

    @patch("app.tools.datarobot_rag.DR_LLM_DEPLOYMENT_ID", None)
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    @patch("app.tools.datarobot_rag._get_openai_client")
    async def test_with_empty_history(
        self, mock_get_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("answer")
        )

        result = await query_datarobot_rag_with_context("question", "")

        assert "answer" in result
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert len(messages) == 1


# ---------------------------------------------------------------------------
# Advanced pipeline helper tests
# ---------------------------------------------------------------------------


class TestOptimizeQuery:
    """Tests for the _optimize_query helper."""

    @patch("app.tools.datarobot_rag._get_llm_client")
    def test_basic_optimization(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("DataRobot pricing plans")
        )

        result = _optimize_query("DataRobotの料金プランについて教えてください")

        assert result == "DataRobot pricing plans"
        mock_client.chat.completions.create.assert_called_once()

    @patch("app.tools.datarobot_rag._get_llm_client")
    def test_optimization_with_conversation_history(
        self, mock_get_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("DataRobot Enterprise pricing details")
        )

        history = [
            {"role": "user", "content": "Tell me about DataRobot"},
            {"role": "assistant", "content": "DataRobot is an AI platform."},
        ]
        result = _optimize_query("How much does the Enterprise plan cost?", history)

        assert result == "DataRobot Enterprise pricing details"
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        # Should include conversation context in the user message
        user_msg = messages[-1]["content"]
        assert "Recent conversation" in user_msg
        assert "Current question" in user_msg

    @patch("app.tools.datarobot_rag._get_llm_client")
    def test_optimization_returns_original_on_empty_response(
        self, mock_get_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("")
        )

        result = _optimize_query("original question")
        assert result == "original question"


class TestFilterChunks:
    """Tests for the _filter_chunks helper."""

    @patch("app.tools.datarobot_rag._get_llm_client")
    def test_filters_relevant_chunks(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("[0, 2]")
        )

        chunks = [
            {"content": "Relevant chunk A", "metadata": {"source": "a.pdf"}},
            {"content": "Irrelevant chunk B", "metadata": {"source": "b.pdf"}},
            {"content": "Relevant chunk C", "metadata": {"source": "c.pdf"}},
        ]
        result = _filter_chunks("test question", chunks)

        assert len(result) == 2
        assert result[0]["content"] == "Relevant chunk A"
        assert result[1]["content"] == "Relevant chunk C"

    def test_empty_chunks_returns_empty(self) -> None:
        result = _filter_chunks("question", [])
        assert result == []

    @patch("app.tools.datarobot_rag._get_llm_client")
    def test_invalid_response_returns_all_chunks(
        self, mock_get_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("not a valid json array")
        )

        chunks = [
            {"content": "chunk A", "metadata": {"source": "a.pdf"}},
            {"content": "chunk B", "metadata": {"source": "b.pdf"}},
        ]
        result = _filter_chunks("question", chunks)

        # Should return all chunks as fallback
        assert len(result) == 2

    @patch("app.tools.datarobot_rag._get_llm_client")
    def test_out_of_range_indices_are_ignored(
        self, mock_get_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("[0, 5, -1]")
        )

        chunks = [
            {"content": "chunk A", "metadata": {"source": "a.pdf"}},
            {"content": "chunk B", "metadata": {"source": "b.pdf"}},
        ]
        result = _filter_chunks("question", chunks)

        # Only index 0 is valid
        assert len(result) == 1
        assert result[0]["content"] == "chunk A"

    @patch("app.tools.datarobot_rag._get_llm_client")
    def test_empty_array_response(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("[]")
        )

        chunks = [
            {"content": "chunk A", "metadata": {"source": "a.pdf"}},
        ]
        result = _filter_chunks("question", chunks)
        assert len(result) == 0


class TestGenerateAnswer:
    """Tests for the _generate_answer helper."""

    @patch("app.tools.datarobot_rag._get_llm_client")
    def test_basic_answer_generation(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("Generated answer based on [1] and [2].")
        )

        chunks = [
            {"content": "Fact one", "metadata": {"source": "doc1.pdf", "page": "1"}},
            {"content": "Fact two", "metadata": {"source": "doc2.pdf"}},
        ]
        result = _generate_answer("What are the facts?", chunks)

        assert "Generated answer based on [1] and [2]." in result

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        # Should have system + user messages
        assert messages[0]["role"] == "system"
        user_msg = messages[-1]["content"]
        assert "Fact one" in user_msg
        assert "Fact two" in user_msg
        assert "doc1.pdf" in user_msg

    @patch("app.tools.datarobot_rag._get_llm_client")
    def test_answer_generation_with_history(
        self, mock_get_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("Contextual answer.")
        )

        chunks = [{"content": "Data", "metadata": {"source": "doc.pdf"}}]
        history = [
            {"role": "user", "content": "Prior question"},
            {"role": "assistant", "content": "Prior answer"},
        ]
        result = _generate_answer("Follow-up?", chunks, history)

        assert result == "Contextual answer."
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        # system + 2 history + user = 4
        assert len(messages) == 4
        assert messages[1]["content"] == "Prior question"
        assert messages[2]["content"] == "Prior answer"

    @patch.dict(
        "os.environ", {"DR_RAG_SYSTEM_PROMPT": "Custom system instructions."}
    )
    @patch("app.tools.datarobot_rag._get_llm_client")
    def test_custom_system_prompt_prepended(
        self, mock_get_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            _make_mock_completion("answer")
        )

        chunks = [{"content": "Data", "metadata": {"source": "doc.pdf"}}]
        _generate_answer("question", chunks)

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert "Custom system instructions." in messages[0]["content"]


# ---------------------------------------------------------------------------
# Advanced pipeline integration tests
# ---------------------------------------------------------------------------


class TestAdvancedRagPipeline:
    """Tests for the _advanced_rag_pipeline orchestration function."""

    @patch("app.tools.datarobot_rag._get_openai_client")
    @patch("app.tools.datarobot_rag._get_llm_client")
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    def test_full_pipeline(
        self, mock_get_llm: MagicMock, mock_get_rag: MagicMock
    ) -> None:
        # LLM client: used for optimize, filter, generate
        llm_client = MagicMock()
        mock_get_llm.return_value = llm_client

        # Step 1: query optimization returns optimized query
        optimize_response = _make_mock_completion("optimized search query")
        # Step 3: chunk filtering returns [0, 1]
        filter_response = _make_mock_completion("[0, 1]")
        # Step 4: answer generation
        generate_response = _make_mock_completion("Final answer from chunks.")

        llm_client.chat.completions.create.side_effect = [
            optimize_response,
            filter_response,
            generate_response,
        ]

        # RAG client: returns answer + citations
        rag_client = MagicMock()
        mock_get_rag.return_value = rag_client
        citations = [
            {"content": "Chunk 1 text", "metadata": {"source": "a.pdf", "page": "1"}},
            {"content": "Chunk 2 text", "metadata": {"source": "b.pdf", "page": "2"}},
        ]
        rag_client.chat.completions.create.return_value = (
            _make_mock_completion("RAG raw answer", citations)
        )

        result = _advanced_rag_pipeline("Tell me about DataRobot pricing")

        # Should use generated answer, not RAG raw answer
        assert "Final answer from chunks." in result
        # Should include references
        assert "a.pdf" in result
        assert "b.pdf" in result

        # LLM client should be called 3 times: optimize, filter, generate
        assert llm_client.chat.completions.create.call_count == 3

        # RAG client should be called once with optimized query
        rag_call = rag_client.chat.completions.create.call_args
        rag_messages = rag_call.kwargs.get("messages") or rag_call[1].get("messages")
        assert any("optimized search query" in m["content"] for m in rag_messages)

    @patch("app.tools.datarobot_rag._get_openai_client")
    @patch("app.tools.datarobot_rag._get_llm_client")
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    def test_pipeline_no_citations_returns_rag_answer(
        self, mock_get_llm: MagicMock, mock_get_rag: MagicMock
    ) -> None:
        llm_client = MagicMock()
        mock_get_llm.return_value = llm_client
        llm_client.chat.completions.create.return_value = (
            _make_mock_completion("optimized query")
        )

        rag_client = MagicMock()
        mock_get_rag.return_value = rag_client
        # No citations returned
        rag_client.chat.completions.create.return_value = (
            _make_mock_completion("RAG answer without citations")
        )

        result = _advanced_rag_pipeline("question")

        assert result == "RAG answer without citations"
        # LLM called only for optimization (no filter/generate since no citations)
        assert llm_client.chat.completions.create.call_count == 1

    @patch("app.tools.datarobot_rag._get_openai_client")
    @patch("app.tools.datarobot_rag._get_llm_client")
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    def test_pipeline_optimization_failure_uses_original(
        self, mock_get_llm: MagicMock, mock_get_rag: MagicMock
    ) -> None:
        llm_client = MagicMock()
        mock_get_llm.return_value = llm_client

        # Optimization raises an error
        error = Exception("LLM unavailable")
        filter_response = _make_mock_completion("[0]")
        generate_response = _make_mock_completion("Generated answer.")

        llm_client.chat.completions.create.side_effect = [
            error,
            filter_response,
            generate_response,
        ]

        rag_client = MagicMock()
        mock_get_rag.return_value = rag_client
        citations = [{"content": "Chunk", "metadata": {"source": "doc.pdf"}}]
        rag_client.chat.completions.create.return_value = (
            _make_mock_completion("RAG answer", citations)
        )

        result = _advanced_rag_pipeline("original question")

        # Should still produce an answer using the original question
        assert "Generated answer." in result

        # RAG should have been called with original question (not optimized)
        rag_call = rag_client.chat.completions.create.call_args
        rag_messages = rag_call.kwargs.get("messages") or rag_call[1].get("messages")
        assert any("original question" in m["content"] for m in rag_messages)

    @patch("app.tools.datarobot_rag._get_openai_client")
    @patch("app.tools.datarobot_rag._get_llm_client")
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    def test_pipeline_generation_failure_returns_fallback(
        self, mock_get_llm: MagicMock, mock_get_rag: MagicMock
    ) -> None:
        llm_client = MagicMock()
        mock_get_llm.return_value = llm_client

        optimize_response = _make_mock_completion("optimized")
        filter_response = _make_mock_completion("[0]")
        generate_error = Exception("Generation failed")

        llm_client.chat.completions.create.side_effect = [
            optimize_response,
            filter_response,
            generate_error,
        ]

        rag_client = MagicMock()
        mock_get_rag.return_value = rag_client
        citations = [{"content": "Chunk text", "metadata": {"source": "doc.pdf"}}]
        rag_client.chat.completions.create.return_value = (
            _make_mock_completion("RAG fallback answer", citations)
        )

        result = _advanced_rag_pipeline("question")

        # Should fall back to RAG answer + citations
        assert "RAG fallback answer" in result
        assert "doc.pdf" in result

    @patch("app.tools.datarobot_rag._get_openai_client")
    @patch("app.tools.datarobot_rag._get_llm_client")
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    def test_pipeline_filter_returns_empty_uses_fallback(
        self, mock_get_llm: MagicMock, mock_get_rag: MagicMock
    ) -> None:
        llm_client = MagicMock()
        mock_get_llm.return_value = llm_client

        optimize_response = _make_mock_completion("optimized")
        # Filter returns empty array = no relevant chunks
        filter_response = _make_mock_completion("[]")

        llm_client.chat.completions.create.side_effect = [
            optimize_response,
            filter_response,
        ]

        rag_client = MagicMock()
        mock_get_rag.return_value = rag_client
        citations = [{"content": "Chunk", "metadata": {"source": "doc.pdf"}}]
        rag_client.chat.completions.create.return_value = (
            _make_mock_completion("RAG answer", citations)
        )

        result = _advanced_rag_pipeline("question")

        # Fallback: RAG answer + all original citations
        assert "RAG answer" in result
        assert "doc.pdf" in result


# ---------------------------------------------------------------------------
# Advanced pipeline via tool functions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestQueryDatarobotRagAdvanced:
    """Tests for query_datarobot_rag when DR_LLM_DEPLOYMENT_ID is set."""

    @patch("app.tools.datarobot_rag._advanced_rag_pipeline")
    @patch("app.tools.datarobot_rag.DR_LLM_DEPLOYMENT_ID", "llm-deploy-456")
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    async def test_uses_advanced_pipeline(
        self, mock_pipeline: MagicMock
    ) -> None:
        mock_pipeline.return_value = "Advanced answer"

        result = await query_datarobot_rag("question")

        assert result == "Advanced answer"
        mock_pipeline.assert_called_once_with("question")

    @patch("app.tools.datarobot_rag._advanced_rag_pipeline")
    @patch("app.tools.datarobot_rag.DR_LLM_DEPLOYMENT_ID", "llm-deploy-456")
    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", "deploy-123")
    async def test_with_context_uses_advanced_pipeline(
        self, mock_pipeline: MagicMock
    ) -> None:
        mock_pipeline.return_value = "Advanced contextual answer"

        history = json.dumps([
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ])
        result = await query_datarobot_rag_with_context("follow-up", history)

        assert result == "Advanced contextual answer"
        mock_pipeline.assert_called_once()
        call_args = mock_pipeline.call_args
        assert call_args[0][0] == "follow-up"
        # Should have parsed conversation history
        conv_history = call_args[1].get("conversation_history") or call_args[0][1]
        assert len(conv_history) == 2
        assert conv_history[0]["content"] == "Hello"
