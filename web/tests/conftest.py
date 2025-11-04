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
from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import create_app


@pytest.fixture(autouse=True)
def patch_env() -> Generator[None, None, None]:
    with patch.dict(os.environ, {"SESSION_SECRET_KEY": "test-secret-key"}):
        yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
