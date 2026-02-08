# DataRobot RAG 対応 実装計画書

## 1. 概要

本計画書は、既存の DataRobot Agent Application（LangGraph ベースのマルチエージェントアプリ）を **DataRobot RAG（Retrieval-Augmented Generation）対応** に改造するための実装計画を記述する。

参考リポジトリ: [datarobot-oss/qa-app-streamlit](https://github.com/datarobot-oss/qa-app-streamlit)

### 現行アーキテクチャ

```
Frontend (React/Vite, port 5173)
    ↓ HTTP/SSE
FastAPI Backend (port 8080)
    ↓
LangGraph Agent (port 8842)
    ↓
MCP Server (port 9000) → LiteLLM → Azure GPT-5-mini
```

### 目標アーキテクチャ

```
Frontend (React/Vite, port 5173)
    ↓ HTTP/SSE
FastAPI Backend (port 8080)
    ↓
LangGraph Agent (port 8842)
    ├→ MCP Server (port 9000)
    │   └→ DataRobot RAG Tool (新規)
    │       └→ DataRobot Deployment (予測API / Chat API)
    │           └→ RAG Pipeline (VectorDB + LLM)
    └→ LiteLLM → LLM (推論・要約用)
```

---

## 2. 参考リポジトリ（qa-app-streamlit）の DataRobot 予測 API ロジック分析

qa-app-streamlit は DataRobot デプロイメントと3つのモードで通信する:

### Mode A: Direct Prediction API（`datarobot-predict` ライブラリ）
- エンドポイント: `/predApi/v1.0/deployments/{id}/predictions`
- 入力: pandas DataFrame（`promptText`, `association_id` カラム）
- 出力: DataFrame（`resultText` + `CITATION_CONTENT_0`, `CITATION_SOURCE_0` 等）
- 認証: DataRobot API Token

### Mode B: OpenAI 互換 Chat API（非ストリーミング）
- エンドポイント: `{endpoint}/deployments/{deployment_id}/chat/completions`
- OpenAI SDK を利用、`model="datarobot-deployed-llm"`
- 認証: `api_key` パラメータに DataRobot API Token
- Citations: `completion.model_extra['citations']`

### Mode C: OpenAI 互換 Chat API（ストリーミング）
- Mode B + `stream=True`
- 最終チャンクに citations/moderation データ

### 本プロジェクトへの適用方針

**Mode B（OpenAI 互換 Chat API）を主軸** に採用する。理由:
1. 既存の LangGraph エージェントのツールとして自然に統合可能
2. OpenAI SDK は既にプロジェクトの依存関係に含まれている
3. 会話履歴の送信が容易（messages 配列をそのまま渡せる）
4. ストリーミング対応が容易

---

## 3. 実装ステップ

### Step 1: 環境変数・設定の追加

**対象ファイル:**
- `.env.template`
- `mcp_server/app/main.py`（設定読み込み）
- `infra/` 配下（Pulumi でのランタイムパラメータ追加）

**追加する環境変数:**

```env
# DataRobot RAG Deployment
DR_RAG_DEPLOYMENT_ID=              # RAG デプロイメントの ID
DR_RAG_ENDPOINT=                   # DataRobot API エンドポイント（既存の DATAROBOT_ENDPOINT を流用可）
DR_RAG_API_TOKEN=                  # DataRobot API トークン（既存の DATAROBOT_API_TOKEN を流用可）
DR_RAG_ENABLE_CHAT_API=true        # Chat API を使用するか（デフォルト: true）
DR_RAG_ENABLE_STREAMING=false      # ストリーミングを有効にするか
DR_RAG_SYSTEM_PROMPT=              # RAG 用のシステムプロンプト（オプション）
```

**作業内容:**
1. `.env.template` に上記変数を追加
2. `metadata.yaml`（MCP Server 用）にランタイムパラメータとして定義
3. Pulumi のランタイムパラメータ設定に追加（`infra/configurations/` 配下）

---

### Step 2: MCP Server に DataRobot RAG ツールを追加

**対象ファイル（新規作成）:**
- `mcp_server/app/tools/datarobot_rag.py`

**対象ファイル（変更）:**
- `mcp_server/pyproject.toml`（依存関係追加）

**実装内容:**

```python
# mcp_server/app/tools/datarobot_rag.py

import os
import json
from typing import Any
from openai import OpenAI
from dr_mcp import dr_mcp_tool

# 設定
DR_RAG_DEPLOYMENT_ID = os.environ.get("DR_RAG_DEPLOYMENT_ID")
DR_RAG_ENDPOINT = os.environ.get("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
DR_RAG_API_TOKEN = os.environ.get("DATAROBOT_API_TOKEN")
DR_RAG_ENABLE_STREAMING = os.environ.get("DR_RAG_ENABLE_STREAMING", "false").lower() == "true"

def _get_openai_client() -> OpenAI:
    """DataRobot の OpenAI 互換エンドポイントに接続する OpenAI クライアントを返す"""
    base_url = f"{DR_RAG_ENDPOINT}/deployments/{DR_RAG_DEPLOYMENT_ID}"
    return OpenAI(base_url=base_url, api_key=DR_RAG_API_TOKEN)

def _format_citations(citations: list[dict]) -> str:
    """引用情報を人間が読めるフォーマットに変換する"""
    if not citations:
        return ""
    parts = ["\n\n---\n**引用元:**"]
    for i, cite in enumerate(citations, 1):
        source = cite.get("metadata", {}).get("source", "不明")
        page = cite.get("metadata", {}).get("page", "")
        content = cite.get("content", "")[:200]  # 長すぎる引用は省略
        parts.append(f"\n[{i}] {source}" + (f" (p.{page})" if page else ""))
        if content:
            parts.append(f"    {content}...")
    return "\n".join(parts)

@dr_mcp_tool()
def query_datarobot_rag(question: str) -> str:
    """DataRobot RAG デプロイメントに質問を送信し、引用付きの回答を取得する。

    社内ドキュメントやナレッジベースに基づいた回答が必要な場合に使用する。
    DataRobot のベクトルデータベースで関連文書を検索し、LLM で回答を生成する。

    Args:
        question: ユーザーからの質問テキスト

    Returns:
        引用情報付きの回答テキスト
    """
    if not DR_RAG_DEPLOYMENT_ID:
        return "エラー: DR_RAG_DEPLOYMENT_ID が設定されていません。"

    client = _get_openai_client()

    messages = [{"role": "user", "content": question}]

    # システムプロンプトがあれば追加
    system_prompt = os.environ.get("DR_RAG_SYSTEM_PROMPT")
    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})

    completion = client.chat.completions.create(
        model="datarobot-deployed-llm",
        messages=messages,
        stream=False,
    )

    content = completion.choices[0].message.content

    # DataRobot 固有の拡張フィールドから引用を取得
    citations = []
    if hasattr(completion, "model_extra") and completion.model_extra:
        citations = completion.model_extra.get("citations", [])

    citation_text = _format_citations(citations)

    return content + citation_text
```

**依存関係の追加（`mcp_server/pyproject.toml`）:**
- `openai >= 1.60.0`（既に間接依存で入っている可能性が高いが明示する）

---

### Step 3: 会話コンテキスト対応の RAG ツール（拡張版）

Step 2 の基本ツールを拡張し、会話履歴を考慮した RAG クエリを可能にする。

**対象ファイル:**
- `mcp_server/app/tools/datarobot_rag.py`（Step 2 のファイルに追加）

**追加するツール:**

```python
@dr_mcp_tool()
def query_datarobot_rag_with_context(
    question: str,
    conversation_history: str = "",
) -> str:
    """会話コンテキストを考慮して DataRobot RAG に質問する。

    過去の会話の流れを踏まえた質問をする場合に使用する。
    conversation_history に過去のやり取りを JSON 形式で渡す。

    Args:
        question: 現在の質問テキスト
        conversation_history: 過去の会話履歴（JSON 文字列、オプション）

    Returns:
        引用情報付きの回答テキスト
    """
    client = _get_openai_client()

    messages = []

    system_prompt = os.environ.get("DR_RAG_SYSTEM_PROMPT")
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # 会話履歴を復元
    if conversation_history:
        try:
            history = json.loads(conversation_history)
            for msg in history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
        except json.JSONDecodeError:
            pass

    messages.append({"role": "user", "content": question})

    completion = client.chat.completions.create(
        model="datarobot-deployed-llm",
        messages=messages,
        stream=False,
    )

    content = completion.choices[0].message.content
    citations = []
    if hasattr(completion, "model_extra") and completion.model_extra:
        citations = completion.model_extra.get("citations", [])

    return content + _format_citations(citations)
```

---

### Step 4: エージェントワークフローの改造

**対象ファイル:**
- `agent/agent/myagent.py`

**変更内容:**

現在のエージェントは Planner → Writer の2ノード構成だが、これを RAG 対応のワークフローに変更する。

#### 4a. 方針 A: 既存ワークフローに RAG ツールを追加（最小変更）

MCP Server に RAG ツールを追加するだけで、LangGraph エージェントは自動的に `self.mcp_tools` 経由で RAG ツールを利用可能になる。エージェントのプロンプトを調整して RAG ツールの使用を促す。

```python
# agent/agent/myagent.py の変更点

@property
def prompt_template(self) -> str:
    return """あなたはナレッジベースに基づいて質問に回答するアシスタントです。

ユーザーの質問に答える際は、まず query_datarobot_rag ツールを使用して
関連するドキュメントを検索してください。検索結果の引用情報を
回答に含めてください。

ユーザーの質問: {topic}"""
```

#### 4b. 方針 B: 専用の RAG ワークフローに再構成（推奨）

```python
# agent/agent/myagent.py

from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START, END

class MyAgent(LangGraphAgent):
    @property
    def prompt_template(self) -> str:
        return "{topic}"

    @property
    def workflow(self) -> StateGraph:
        """RAG 対応のワークフローを構築する"""
        builder = StateGraph(MessagesState)

        # RAG エージェント: DataRobot RAG ツールを使って情報を検索・回答
        rag_agent = create_react_agent(
            self.llm,
            tools=self.mcp_tools,
            prompt=(
                "あなたは社内ナレッジベースに基づいて正確に回答するアシスタントです。\n"
                "ユーザーの質問に答えるために、query_datarobot_rag ツールを使用して "
                "関連するドキュメントを検索してください。\n"
                "回答には必ず引用元を含めてください。\n"
                "情報が見つからない場合は、その旨を正直に伝えてください。"
            ),
        )

        builder.add_node("rag_agent", rag_agent)
        builder.add_edge(START, "rag_agent")
        builder.add_edge("rag_agent", END)

        return builder
```

**推奨: 方針 B** を採用。理由:
- ワークフローが RAG 用途に最適化される
- プロンプトが明確で、不要なツール呼び出しを防げる
- 将来的にノードを追加（要約、フィルタリング等）しやすい

---

### Step 5: フロントエンドの引用表示対応

**対象ファイル（変更）:**
- `frontend_web/src/pages/Chat.tsx`
- `frontend_web/src/components/`（必要に応じて新規コンポーネント）

**実装内容:**

RAG の回答に含まれる引用情報をユーザーフレンドリーに表示する。

引用はツールの出力テキストに含まれる形式で返されるため、フロントエンドではマークダウンレンダリングで対応可能。追加のパースが必要な場合:

```typescript
// frontend_web/src/components/Citations.tsx（新規）

interface Citation {
  source: string;
  page?: string;
  content: string;
}

function parseCitations(text: string): { answer: string; citations: Citation[] } {
  const separator = "---\n**引用元:**";
  const parts = text.split(separator);
  if (parts.length < 2) return { answer: text, citations: [] };

  const answer = parts[0].trim();
  const citationBlock = parts[1];

  // [N] source (p.X) 形式をパース
  const citations: Citation[] = [];
  const regex = /\[(\d+)\]\s+(.+?)(?:\s+\(p\.(.+?)\))?\n\s{4}(.+?)(?:\.\.\.|$)/g;
  let match;
  while ((match = regex.exec(citationBlock)) !== null) {
    citations.push({
      source: match[2],
      page: match[3],
      content: match[4],
    });
  }

  return { answer, citations };
}
```

ただし、既存のチャット UI はマークダウンレンダリング機能を持っているため、Step 2 のツール出力に含まれる引用テキストはそのまま表示可能。初期実装ではフロントエンド変更は最小限とし、必要に応じて拡張する。

---

### Step 6: Direct Prediction API のフォールバック対応（オプション）

Chat API 非対応のデプロイメントにも対応する場合の追加実装。

**対象ファイル:**
- `mcp_server/app/tools/datarobot_rag.py`
- `mcp_server/pyproject.toml`（`datarobot-predict` 追加）

**実装内容:**

```python
import requests
import pandas as pd

def _check_chat_api_support() -> bool:
    """デプロイメントが Chat API をサポートするか確認する"""
    url = f"{DR_RAG_ENDPOINT}/deployments/{DR_RAG_DEPLOYMENT_ID}/capabilities/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {DR_RAG_API_TOKEN}",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        chat_cap = next(
            (item for item in data.get("data", []) if item["name"] == "supports_chat_api"),
            {},
        )
        return chat_cap.get("supported", False)
    except Exception:
        return False

def _send_predict_request(question: str) -> tuple[str, list]:
    """Direct Prediction API を使用してクエリする"""
    from datarobot_predict.deployment import predict
    import datarobot as dr

    dr.Client(token=DR_RAG_API_TOKEN, endpoint=DR_RAG_ENDPOINT)
    deployment = dr.Deployment.get(DR_RAG_DEPLOYMENT_ID)

    input_df = pd.DataFrame({
        "promptText": [question],
        "association_id": [str(uuid.uuid4())],
    })

    result_df, _ = predict(deployment, input_df)

    # 結果カラムから回答テキストを取得
    answer = result_df.get("resultText", result_df.iloc[0]).iloc[0]

    # 引用情報を取得
    citations = []
    i = 0
    while f"CITATION_CONTENT_{i}" in result_df.columns:
        citations.append({
            "content": result_df[f"CITATION_CONTENT_{i}"].iloc[0],
            "metadata": {
                "source": result_df.get(f"CITATION_SOURCE_{i}", pd.Series([""])).iloc[0],
                "page": result_df.get(f"CITATION_PAGE_{i}", pd.Series([""])).iloc[0],
            },
        })
        i += 1

    return answer, citations
```

---

### Step 7: テストの追加

**対象ファイル（新規作成）:**
- `mcp_server/tests/test_datarobot_rag.py`
- `agent/tests/test_rag_workflow.py`

**テスト内容:**

```python
# mcp_server/tests/test_datarobot_rag.py

import pytest
from unittest.mock import patch, MagicMock

class TestDataRobotRAGTool:
    """DataRobot RAG ツールのユニットテスト"""

    def test_query_rag_success(self):
        """正常系: 引用付きの回答が返される"""
        ...

    def test_query_rag_no_deployment_id(self):
        """異常系: DEPLOYMENT_ID 未設定"""
        ...

    def test_query_rag_api_error(self):
        """異常系: API エラー時の処理"""
        ...

    def test_format_citations(self):
        """引用フォーマットのテスト"""
        ...

    def test_query_with_conversation_history(self):
        """会話履歴付きクエリのテスト"""
        ...
```

---

## 4. ファイル変更一覧

| ファイル | 操作 | 内容 |
|---------|------|------|
| `.env.template` | 変更 | RAG 関連の環境変数を追加 |
| `mcp_server/app/tools/datarobot_rag.py` | **新規** | DataRobot RAG ツール本体 |
| `mcp_server/pyproject.toml` | 変更 | `openai` 依存を追加 |
| `agent/agent/myagent.py` | 変更 | ワークフローを RAG 対応に変更 |
| `frontend_web/src/components/Citations.tsx` | **新規**（オプション） | 引用表示コンポーネント |
| `mcp_server/tests/test_datarobot_rag.py` | **新規** | RAG ツールのテスト |
| `agent/tests/test_rag_workflow.py` | **新規** | ワークフローのテスト |
| `infra/` 配下 | 変更 | ランタイムパラメータに RAG 設定を追加 |
| `mcp_server/app/tools/__init__.py` | 変更（必要に応じて） | ツール登録 |

---

## 5. 実装の優先順位

| フェーズ | タスク | 必須/任意 |
|---------|--------|----------|
| **Phase 1** | Step 1: 環境変数・設定の追加 | 必須 |
| **Phase 1** | Step 2: MCP RAG ツール（基本版） | 必須 |
| **Phase 1** | Step 4b: エージェントワークフロー改造 | 必須 |
| **Phase 2** | Step 3: 会話コンテキスト対応 | 推奨 |
| **Phase 2** | Step 7: テスト追加 | 推奨 |
| **Phase 3** | Step 5: フロントエンド引用表示 | 任意 |
| **Phase 3** | Step 6: Direct Prediction API フォールバック | 任意 |

---

## 6. 前提条件・必要な準備

1. **DataRobot RAG デプロイメント**: DataRobot 上に RAG パイプライン（ベクトルデータベース + LLM）がデプロイ済みであること
2. **デプロイメント ID**: 対象の RAG デプロイメントの ID を取得済みであること
3. **API トークン**: DataRobot API への認証トークンが発行済みであること
4. **Chat API 対応確認**: 対象デプロイメントが OpenAI 互換 Chat API をサポートしているか確認すること

---

## 7. リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| RAG デプロイメントの応答遅延 | ユーザー体験の低下 | タイムアウト設定、ストリーミング対応 |
| 引用フォーマットの変更 | 引用表示の崩れ | パーサーを柔軟に実装、テストで検証 |
| Chat API 非サポート | API 呼び出し失敗 | Capabilities チェック + Predict API フォールバック |
| トークン上限超過 | 長い会話での API エラー | 会話履歴の要約・切り詰め処理 |
| MCP ツール発見の失敗 | エージェントが RAG を使えない | ツール登録のテスト、ログ出力 |

---

## 8. 技術的な設計判断

### なぜ MCP ツールとして実装するか

DataRobot RAG を MCP Server のツールとして実装する理由:

1. **既存アーキテクチャとの整合性**: MCP Server がツールのハブとして機能しており、新しいツールの追加パターンが確立されている
2. **エージェントの自律性**: LangGraph エージェントが状況に応じて RAG ツールを使うか判断できる
3. **再利用性**: 他のエージェントやワークフローからも同じ RAG ツールを利用可能
4. **関心の分離**: RAG のロジックがエージェントから分離され、テストと保守が容易

### なぜ OpenAI 互換 Chat API を主軸にするか

1. **コードの簡潔さ**: OpenAI SDK をそのまま使えるため実装量が少ない
2. **会話履歴対応**: messages 配列で自然にマルチターン会話を表現可能
3. **拡張フィールド**: `model_extra` から citations 等の DataRobot 固有データにアクセス可能
4. **業界標準**: OpenAI 互換 API は広く採用されており、将来の変更リスクが低い
