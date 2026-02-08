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
    """Advanced RAG agent with query optimization, search, and answer refinement.

    Uses a three-node workflow:
      1. Query Optimizer  – rewrites the user's question into search-friendly terms.
      2. RAG Searcher     – calls the RAG deployment to retrieve relevant chunks.
      3. Answer Refiner   – evaluates retrieved chunks and generates a refined answer.
    """

    @property
    def workflow(self) -> StateGraph[MessagesState]:
        langgraph_workflow = StateGraph[
            MessagesState, None, MessagesState, MessagesState
        ](MessagesState)

        langgraph_workflow.add_node("query_optimizer", self.agent_query_optimizer)
        langgraph_workflow.add_node("rag_searcher", self.agent_rag_searcher)
        langgraph_workflow.add_node("answer_refiner", self.agent_answer_refiner)

        langgraph_workflow.add_edge(START, "query_optimizer")
        langgraph_workflow.add_edge("query_optimizer", "rag_searcher")
        langgraph_workflow.add_edge("rag_searcher", "answer_refiner")
        langgraph_workflow.add_edge("answer_refiner", END)

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

    # ------------------------------------------------------------------
    # Node 1: Query Optimizer
    # ------------------------------------------------------------------

    @property
    def agent_query_optimizer(self) -> Any:
        """Rewrites the user's question into an optimized vector-search query."""
        return create_react_agent(
            self.llm(),
            tools=self.mcp_tools,
            prompt=make_system_prompt(
                "You are a search query optimization specialist.\n"
                "\n"
                "Your task is to rewrite the user's question into an optimized query "
                "for vector database retrieval. Follow these rules:\n"
                "1. Remove greetings, filler words, and unnecessary context.\n"
                "2. Extract key concepts, entities, and technical terms.\n"
                "3. Include synonyms or related terms that might appear in documents.\n"
                "4. If the conversation history suggests the question is a follow-up, "
                "resolve pronouns and references (e.g., replace 'it' or 'that' with "
                "the actual subject from previous messages).\n"
                "5. Keep the query concise but comprehensive.\n"
                "6. Maintain the language of the original question.\n"
                "\n"
                "Output ONLY the optimized search query text. Do NOT answer the "
                "question yourself, do NOT add any explanation, and do NOT use any tools.",
            ),
            name="Query Optimizer",
        )

    # ------------------------------------------------------------------
    # Node 2: RAG Searcher
    # ------------------------------------------------------------------

    @property
    def agent_rag_searcher(self) -> Any:
        """Searches the knowledge base using the optimized query."""
        return create_react_agent(
            self.llm(),
            tools=self.mcp_tools,
            prompt=make_system_prompt(
                "You are a document search agent.\n"
                "\n"
                "The previous assistant message contains an optimized search query. "
                "Your job is to use that query to search the knowledge base.\n"
                "\n"
                "Instructions:\n"
                "1. Extract the optimized search query from the previous assistant message.\n"
                "2. Call the query_datarobot_rag tool with that query as the 'question' "
                "parameter. Do NOT modify the query.\n"
                "3. Return the complete tool response including all references and "
                "citations exactly as received. Do NOT summarize or rewrite the results.\n"
                "\n"
                "If the user's question seems to be a follow-up that requires "
                "conversation context, use query_datarobot_rag_with_context instead.",
            ),
            name="RAG Searcher",
        )

    # ------------------------------------------------------------------
    # Node 3: Answer Refiner
    # ------------------------------------------------------------------

    @property
    def agent_answer_refiner(self) -> Any:
        """Evaluates retrieved chunks and generates a refined answer."""
        return create_react_agent(
            self.llm(),
            tools=self.mcp_tools,
            prompt=make_system_prompt(
                "You are an answer quality specialist.\n"
                "\n"
                "You have access to the following context from earlier in this "
                "conversation:\n"
                "- The user's ORIGINAL question (the first human message).\n"
                "- Search results with references retrieved from the knowledge base "
                "(in the previous assistant message).\n"
                "\n"
                "Your task:\n"
                "1. EVALUATE: Review each reference/citation from the search results. "
                "Determine which references are genuinely relevant to the user's "
                "original question and which are not.\n"
                "2. GENERATE: Compose a comprehensive answer using ONLY information "
                "from the relevant references. Include numbered citation markers "
                "(e.g., [1], [2]) when referencing specific sources.\n"
                "3. CITE: Append a References section at the end listing the sources "
                "you actually used.\n"
                "\n"
                "Rules:\n"
                "- Do NOT use any tools. Work only with the information already provided.\n"
                "- Do NOT fabricate information. If no relevant information was found, "
                "honestly tell the user.\n"
                "- Answer in the same language as the user's original question.\n"
                "- Be comprehensive but concise.",
            ),
            name="Answer Refiner",
        )
