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
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import Response

from app.tools.google_drive import list_files_in_google_drive


@pytest.fixture
def mock_google_drive_response() -> dict[str, Any]:
    return {
        "files": [
            {
                "id": "1abc123",
                "name": "Test Document.pdf",
                "mimeType": "application/pdf",
                "size": "1024000",
            },
            {
                "id": "2def456",
                "name": "Spreadsheet.xlsx",
                "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "size": "2048000",
            },
            {
                "id": "3ghi789",
                "name": "Presentation.pptx",
                "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "size": "4096000",
            },
        ],
        "nextPageToken": None,
    }


@pytest.fixture
def mock_oauth_token() -> str:
    return "test-access-token"


@pytest.fixture
def expected_file_names() -> list[str]:
    return ["Test Document.pdf", "Spreadsheet.xlsx", "Presentation.pptx"]


@pytest.fixture
async def mock_google_drive_api(
    mock_google_drive_response: dict[str, Any],
) -> AsyncGenerator[respx.Route, None]:
    """Mock the Google Drive API endpoint."""
    async with respx.mock:
        route = respx.get("https://www.googleapis.com/drive/v3/files").mock(
            return_value=Response(200, json=mock_google_drive_response)
        )
        yield route


@pytest.fixture
def mock_oauth_service(mock_oauth_token: str) -> AsyncGenerator[AsyncMock, None]:
    """Mock the DataRobot OAuth token retrieval."""
    with patch(
        "app.tools.google_drive.get_access_token", new_callable=AsyncMock
    ) as mock_get_token:
        mock_get_token.return_value = mock_oauth_token
        yield mock_get_token


@pytest.mark.asyncio
class TestGoogleDriveIntegration:
    """
    Integration tests for Google Drive MCP tools.

    These tests use mocking to avoid requiring actual external connectivity
    to Google Drive or DataRobot OAuth services.
    """

    async def test_list_files_in_google_drive(
        self,
        mock_google_drive_api: respx.Route,
        mock_oauth_service: AsyncMock,
        expected_file_names: list[str],
    ) -> None:
        result_text: str = await list_files_in_google_drive(offset=0, limit=10)
        result = json.loads(result_text)

        # Verify the response structure
        assert "files" in result or "data" in result, f"Result: {result_text}"

        # The result uses "data" key for the files list
        assert "data" in result
        assert result["count"] == 3
        assert result["offset"] == 0
        assert result["limit"] == 10
        assert len(result["data"]) == 3

        # Verify the mocked data appears in the response
        result_file_names = [file["name"] for file in result["data"]]
        for expected_name in expected_file_names:
            assert expected_name in result_file_names, (
                f"Expected '{expected_name}' in result: {result_file_names}"
            )

        # Verify the mocks were called correctly
        assert mock_oauth_service.called, (
            "OAuth token retrieval should have been called"
        )
        mock_oauth_service.assert_called_once_with("google")

        assert mock_google_drive_api.called, "Google Drive API should have been called"
