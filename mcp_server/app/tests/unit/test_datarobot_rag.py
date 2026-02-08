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
    _format_citations,
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


@pytest.mark.asyncio
class TestQueryDatarobotRag:
    """Tests for the query_datarobot_rag tool."""

    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", None)
    async def test_no_deployment_id(self) -> None:
        result = await query_datarobot_rag("test question")
        assert "Error" in result
        assert "DR_RAG_DEPLOYMENT_ID" in result

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
    """Tests for the query_datarobot_rag_with_context tool."""

    @patch("app.tools.datarobot_rag.DR_RAG_DEPLOYMENT_ID", None)
    async def test_no_deployment_id(self) -> None:
        result = await query_datarobot_rag_with_context("question")
        assert "Error" in result

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
