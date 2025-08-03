# TinyTroupe Brainstorming - コード構造ドキュメント

## 概要

このドキュメントは、TinyTroupe Brainstormingアプリケーションの議論機能における重複実装と構造を整理したものです。

## 問題点

**「議論テーマ「」という文字列が4箇所で重複実装されており、以下の構造的問題があります**:

1. **機能の重複実装** - 議論生成ロジックが複数箇所に散在
2. **保守性の問題** - 同じ機能を複数箇所で修正する必要
3. **一貫性の欠如** - 実装方式が統一されていない

## 現在の実装構造

### 1. 議論実行の3つのアプローチ

#### A. **通常の議論実行** (`app/api/discussions.py`)
```python
# バックエンドタスクとして実行
async def run_discussion_background(discussion_id: int, db: Session)
async def start_discussion(discussion_id: int, background_tasks: BackgroundTasks)
```
- **用途**: シンプルな非同期議論実行
- **戻り値**: レスポンス後にバックグラウンドで処理
- **状態管理**: データベースの`status`フィールドで管理

#### B. **Server-Sent Events (SSE)** (`app/api/discussions.py`)
```python
# リアルタイムストリーミング
async def run_discussion_with_streaming(discussion_id: int, db: Session)
async def stream_discussion_progress(discussion_id: int, db: Session)
```
- **用途**: 進捗をリアルタイムでブラウザに配信
- **戻り値**: StreamingResponse (text/event-stream)
- **状態管理**: グローバル辞書`discussion_streams`

#### C. **WebSocket** (`app/api/websocket_discussions.py`)
```python
# 双方向リアルタイム通信
async def websocket_discussion_endpoint(websocket: WebSocket, discussion_id: int)
async def run_discussion_with_websocket(discussion_id: int, db: Session)
```
- **用途**: より確実なリアルタイム通信と再接続機能
- **戻り値**: WebSocket通信
- **状態管理**: ConnectionManagerクラス

### 2. 議論生成の重複実装 (`app/services/tinytroupe_service.py`)

#### **通常版** (4つのメソッド)
```python
async def run_discussion()                          # メインエントリーポイント
async def _create_tinytroupe_discussion_result()    # TinyTroupe使用
async def _create_ai_discussion_result()            # OpenAI Direct使用  
def _create_mock_discussion_result()                # モックデータ
```

#### **ストリーミング版** (4つのメソッド - 重複)
```python
async def run_discussion_with_streaming()           # ストリーミング用エントリーポイント
async def _create_tinytroupe_streaming_discussion_result()  # TinyTroupe + ストリーミング
async def _create_ai_streaming_discussion_result()          # OpenAI + ストリーミング
async def _create_mock_streaming_discussion_result()        # モック + ストリーミング
```

**⚠️ 問題**: 実質的に同じロジックが2セット存在し、メンテナンスコストが高い

### 3. フロントエンド実装

#### **現在使用中**: `DiscussionResultsPageSimple.tsx`
- ポーリングベースの議論状態監視
- シンプルで確実な動作
- エラーハンドリングとタイムアウト機能

#### **実装済み（未使用）**: `DiscussionResultsPage.tsx`
- Server-Sent Events使用
- 複雑なストリーミングロジック

#### **実装済み（未使用）**: `DiscussionResultsPageWebSocket.tsx`
- WebSocket使用
- 再接続機能付き

## 推奨リファクタリング

### 1. 議論生成の統合

```python
# 統合後の構造（推奨）
class TinyTroupeService:
    async def run_discussion(self, discussion, characters, world, streaming_callback=None):
        """
        統合された議論実行メソッド
        streaming_callback: オプション、リアルタイム更新用
        """
        if streaming_callback:
            # ストリーミング対応
            return await self._run_with_streaming(discussion, characters, world, streaming_callback)
        else:
            # 通常実行
            return await self._run_normal(discussion, characters, world)
    
    async def _run_with_fallback(self, method_name, *args):
        """
        TinyTroupe → OpenAI → Mock のフォールバック実行
        重複ロジックを統合
        """
        for provider in ['tinytroupe', 'openai', 'mock']:
            try:
                method = getattr(self, f'_{method_name}_{provider}')
                return await method(*args)
            except Exception as e:
                logger.warning(f"{provider} failed: {e}")
                continue
```

### 2. API エンドポイントの整理

```python
# 推奨統合構造
@router.post("/{discussion_id}/start")
async def start_discussion(discussion_id: int, stream_type: str = "none"):
    """
    stream_type: "none" | "sse" | "websocket"
    """
    if stream_type == "sse":
        return stream_discussion_progress(discussion_id)
    elif stream_type == "websocket":
        # WebSocket接続へリダイレクト
        pass
    else:
        # 通常のバックグラウンド実行
        pass
```

### 3. 重複コードの除去箇所

| ファイル | 行数 | 重複内容 |
|---------|------|----------|
| `tinytroupe_service.py:342` | 1 | システムメッセージ生成 |
| `tinytroupe_service.py:439` | 1 | システムメッセージ生成 |
| `tinytroupe_service.py:737` | 1 | システムメッセージ生成 |
| `tinytroupe_service.py:823` | 1 | システムメッセージ生成 |

**推奨**: `_create_system_message(discussion)` メソッドを作成

## 現在の運用上の注意

### 有効な実装
- ✅ `DiscussionResultsPageSimple.tsx` - 安定動作
- ✅ `discussions.py` の通常実行 - 基本機能
- ✅ `tinytroupe_service.py` の通常版メソッド

### 実装済みだが未使用
- ⚠️ SSE版 - 動作するが複雑
- ⚠️ WebSocket版 - 高機能だが現在不要
- ⚠️ ストリーミング版TinyTroupeService - 重複実装

### 推奨アクション

1. **短期** (保守性向上)
   - 重複する「議論テーマ「」メッセージを共通メソッド化
   - 使用していないページコンポーネントを整理

2. **中期** (アーキテクチャ改善)
   - TinyTroupeServiceの通常版とストリーミング版を統合
   - APIエンドポイントの整理統合

3. **長期** (機能拡張)
   - 必要に応じてWebSocket版を本格採用
   - リアルタイム機能の段階的実装

## ファイル別責務整理

| ファイル | 責務 | 状態 |
|---------|------|------|
| `discussions.py` | REST API, バックグラウンド実行 | ✅ 主要 |
| `websocket_discussions.py` | WebSocket API | 🔶 実装済み・未使用 |
| `tinytroupe_service.py` | 議論生成ロジック | ⚠️ 重複あり |
| `DiscussionResultsPageSimple.tsx` | UI (ポーリング) | ✅ 現在使用 |
| `DiscussionResultsPage.tsx` | UI (SSE) | 🔶 実装済み・未使用 |
| `DiscussionResultsPageWebSocket.tsx` | UI (WebSocket) | 🔶 実装済み・未使用 |

このドキュメントは2025年8月4日時点の構造分析です。