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
from typing import Any

from datarobot_genai.core.agents import (
    make_system_prompt,
)
from datarobot_genai.langgraph.agent import LangGraphAgent
from langchain_core.prompts import ChatPromptTemplate
from langchain_litellm.chat_models import ChatLiteLLM
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent

from agent.config import Config

config = Config()


class MyAgent(LangGraphAgent):
    """RAG agent that answers questions using a DataRobot RAG deployment.

    Queries the DataRobot RAG deployment through the MCP tool to search
    internal documents / knowledge bases and return answers with citations.
    """

    @property
    def workflow(self) -> StateGraph[MessagesState]:
        langgraph_workflow = StateGraph[
            MessagesState, None, MessagesState, MessagesState
        ](MessagesState)

        langgraph_workflow.add_node("rag_agent", self.agent_rag)
        langgraph_workflow.add_edge(START, "rag_agent")
        langgraph_workflow.add_edge("rag_agent", END)

        return langgraph_workflow  # type: ignore[return-value]

    @property
    def prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                (
                    "user",
                    "{topic}",
                ),
            ]
        )

    def llm(
        self,
        preferred_model: str | None = None,
        auto_model_override: bool = True,
    ) -> ChatLiteLLM:
        """Returns the ChatLiteLLM to use for a given model.

        If a `preferred_model` is provided, it will be used. Otherwise, the default model will be used.
        If auto_model_override is True, it will try and use the model specified in the request
        but automatically back out to the default model if the LLM Gateway is not configured

        Args:
            preferred_model: Optional[str]: The model to use. If none, it defaults to config.llm_default_model.
            auto_model_override: Optional[bool]: If True, it will try and use the model
                specified in the request but automatically back out if the LLM Gateway is
                not available.

        Returns:
            ChatLiteLLM: The model to use.
        """
        api_base = self.litellm_api_base(config.llm_deployment_id)
        model = preferred_model
        if preferred_model is None:
            model = config.llm_default_model
        if auto_model_override and not config.use_datarobot_llm_gateway:
            model = config.llm_default_model
        if self.verbose:
            print(f"Using model: {model}")
        return ChatLiteLLM(
            model=model,
            api_base=api_base,
            api_key=self.api_key,
            timeout=self.timeout,
            streaming=True,
            max_retries=3,
        )

    @property
    def agent_rag(self) -> Any:
        """RAG agent node that searches knowledge bases and answers questions."""
        return create_react_agent(
            self.llm(),
            tools=self.mcp_tools,
            prompt=make_system_prompt(
                "You are a knowledgeable assistant that answers questions based on "
                "internal documents and knowledge bases.\n"
                "\n"
                "When a user asks a question, use the query_datarobot_rag tool to "
                "search for relevant documents and retrieve an answer. If the user's "
                "question requires follow-up context from previous messages, use the "
                "query_datarobot_rag_with_context tool instead.\n"
                "\n"
                "Guidelines:\n"
                "1. Always use the RAG tool to search for information before answering.\n"
                "2. Pass the user's question to the RAG tool's 'question' parameter. "
                "The tool internally handles query optimization for better search "
                "results, so pass the original question without modification.\n"
                "3. Include citation references from the tool's response in your answer.\n"
                "4. If the RAG tool does not return relevant information, honestly tell "
                "the user that the information was not found in the knowledge base.\n"
                "5. Do not fabricate information. Only use facts from the retrieved documents.\n"
                "6. Answer in the same language as the user's question.",
            ),
            name="RAG Agent",
        )
