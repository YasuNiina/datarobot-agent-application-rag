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


from typing import Sequence

from core.telemetry.logging import FormatType, LogLevel
from datarobot.core.config import DataRobotAppFrameworkBaseSettings

from app.auth.oauth import OAuthImpl


class Config(DataRobotAppFrameworkBaseSettings):
    session_secret_key: str

    datarobot_endpoint: str
    datarobot_api_token: str

    session_max_age: int = 14 * 24 * 60 * 60  # 14 days, in seconds
    session_https_only: bool = True
    session_cookie_name: str = "sess"  # Can be overridden for different apps

    log_level: LogLevel = LogLevel.INFO
    log_format: FormatType = "json"

    agent_endpoint: str = "http://localhost:8842"

    oauth_impl: OAuthImpl = OAuthImpl.DATAROBOT
    datarobot_oauth_providers: Sequence[str] = ()

    google_client_id: str | None = None
    google_client_secret: str | None = None

    box_client_id: str | None = None
    box_client_secret: str | None = None

    # these two configs should help to emulate the DataRobot Custom App Authentication like in a deployment application but locally,
    # so you can assume the user and be able to open the UI in the browser without any other configurations.
    # If both are set at the same time, only the DR API key will be used to authenticate the user.
    test_user_api_key: str | None = None
    test_user_email: str | None = None

    database_uri: str = "sqlite+aiosqlite:///.data/database.sqlite"

    # The number of characters to stream before persisting
    minimal_chunks_to_persist: int = 5000
