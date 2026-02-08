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
                "あなたは検索クエリ最適化の専門家です。\n"
                "\n"
                "あなたのタスクは、ユーザーの質問をベクトルデータベース検索に最適化された"
                "クエリに書き換えることです。以下のルールに従ってください：\n"
                "1. 挨拶、つなぎ言葉、不要な文脈を削除する。\n"
                "2. 主要な概念、エンティティ、専門用語を抽出する。\n"
                "3. ドキュメントに含まれる可能性のある同義語や関連用語を含める。\n"
                "4. 会話履歴からフォローアップの質問であると判断される場合、代名詞や"
                "指示語を解決する（例：「それ」や「あれ」を前のメッセージの実際の"
                "主題に置き換える）。\n"
                "5. クエリは簡潔かつ包括的に保つ。\n"
                "6. 元の質問の言語を維持する。\n"
                "\n"
                "最適化された検索クエリテキストのみを出力してください。質問に自分で"
                "回答したり、説明を追加したり、ツールを使用したりしないでください。",
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
                "あなたはドキュメント検索エージェントです。\n"
                "\n"
                "前のアシスタントメッセージには最適化された検索クエリが含まれています。"
                "あなたの仕事は、そのクエリを使用してナレッジベースを検索することです。\n"
                "\n"
                "手順：\n"
                "1. 前のアシスタントメッセージから最適化された検索クエリを抽出する。\n"
                "2. そのクエリを 'question' パラメータとして query_datarobot_rag ツールを"
                "呼び出す。クエリを変更しないこと。\n"
                "3. 参照や引用を含むツールの応答をそのまま完全に返す。結果を要約したり"
                "書き換えたりしないこと。\n"
                "\n"
                "ユーザーの質問が会話のコンテキストを必要とするフォローアップである"
                "場合は、代わりに query_datarobot_rag_with_context を使用してください。",
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
                "あなたは回答品質の専門家です。\n"
                "\n"
                "この会話の中で、以下のコンテキストにアクセスできます：\n"
                "- ユーザーの元の質問（最初のヒューマンメッセージ）。\n"
                "- ナレッジベースから取得された参照付きの検索結果"
                "（前のアシスタントメッセージ内）。\n"
                "\n"
                "あなたのタスク：\n"
                "1. 評価：検索結果の各参照・引用をレビューする。どの参照がユーザーの"
                "元の質問に本当に関連しているか、どれが関連していないかを判断する。\n"
                "2. 生成：関連する参照からの情報のみを使用して、包括的な回答を作成する。"
                "特定のソースを参照する際は、番号付きの引用マーカー"
                "（例：[1]、[2]）を含める。\n"
                "3. 引用：実際に使用したソースを一覧にした参考文献セクションを末尾に"
                "追加する。\n"
                "\n"
                "ルール：\n"
                "- ツールを使用しないこと。既に提供された情報のみで作業する。\n"
                "- 情報を捏造しないこと。関連する情報が見つからなかった場合は、"
                "正直にユーザーに伝える。\n"
                "- ユーザーの元の質問と同じ言語で回答する。\n"
                "- 包括的かつ簡潔に回答する。",
            ),
            name="Answer Refiner",
        )
