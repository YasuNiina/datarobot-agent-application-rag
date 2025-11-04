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

from fastapi import APIRouter

from app.agent.api import add_agui_agent_fastapi_endpoint
from app.agent.dr import DataRobotAGUIAgent
from app.config import Config

config = Config()

writer_agent_router = APIRouter(tags=["writer-agent"])

writer_agent = DataRobotAGUIAgent(name="datarobot", url=config.writer_agent_endpoint)

add_agui_agent_fastapi_endpoint(
    writer_agent_router,
    writer_agent,
    path="/writer-agent",
)
