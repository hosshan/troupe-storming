# リファクタリング計画 - 重複コード統合

## 現在の重複箇所

### 1. 「議論テーマ「」メッセージの重複（4箇所）

**現在の重複コード**:
```python
# tinytroupe_service.py:342, 439, 737, 823
"content": f"議論テーマ「{discussion.theme}」について話し合いを開始します。",
```

**統合案**:
```python
class TinyTroupeService:
    def _create_system_message(self, discussion) -> dict:
        """議論開始システムメッセージを生成"""
        return {
            "speaker": "システム",
            "content": f"議論テーマ「{discussion.theme}」について話し合いを開始します。",
            "timestamp": datetime.datetime.now().isoformat()
        }
```

### 2. 議論生成メソッドの重複

**現在の構造（重複）**:
```
run_discussion() 
├── _create_tinytroupe_discussion_result()
├── _create_ai_discussion_result() 
└── _create_mock_discussion_result()

run_discussion_with_streaming() [重複]
├── _create_tinytroupe_streaming_discussion_result() [重複]
├── _create_ai_streaming_discussion_result() [重複]
└── _create_mock_streaming_discussion_result() [重複]
```

**統合後の構造（推奨）**:
```
async def run_discussion(discussion, characters, world, stream_data=None):
    """統合された議論実行メソッド"""
    providers = ['tinytroupe', 'openai', 'mock']
    
    for provider in providers:
        try:
            if provider == 'tinytroupe' and self.tinytroupe_available and self.api_key:
                return await self._create_discussion_result(
                    'tinytroupe', discussion, characters, world, stream_data
                )
            elif provider == 'openai' and self.openai_available and self.api_key:
                return await self._create_discussion_result(
                    'openai', discussion, characters, world, stream_data
                )
            else:  # mock
                return await self._create_discussion_result(
                    'mock', discussion, characters, world, stream_data
                )
        except Exception as e:
            logger.warning(f"{provider} provider failed: {e}")
            continue

async def _create_discussion_result(self, provider, discussion, characters, world, stream_data=None):
    """プロバイダー別議論生成（ストリーミング対応）"""
    # 共通処理
    messages = [self._create_system_message(discussion)]
    if stream_data:
        stream_data["messages"] = messages
    
    if provider == 'tinytroupe':
        return await self._generate_tinytroupe_discussion(...)
    elif provider == 'openai':
        return await self._generate_openai_discussion(...)
    else:  # mock
        return await self._generate_mock_discussion(...)
```

## 実装手順

### Phase 1: 共通メソッド抽出
```python
# 1. システムメッセージの統合
def _create_system_message(self, discussion):
    # 4箇所の重複を1箇所に統合

# 2. 共通のレスポンス形式生成
def _create_discussion_response(self, discussion, world, characters, messages, note):
    return {
        "discussion_id": discussion.id,
        "theme": discussion.theme,
        "world": world.name,
        "participants": [char.name for char in characters],
        "messages": messages,
        "status": "completed",
        "note": note
    }
```

### Phase 2: メソッド統合
```python
# 通常版とストリーミング版の統合
async def run_discussion(self, discussion, characters, world, stream_callback=None):
    """
    stream_callback: Optional[Callable] - ストリーミング更新用コールバック
    """
    # 統合ロジック実装
```

### Phase 3: 未使用コードの整理
```bash
# 削除対象ファイル
rm frontend/src/pages/DiscussionResultsPage.tsx              # SSE版（未使用）
rm frontend/src/pages/DiscussionResultsPageWebSocket.tsx    # WebSocket版（未使用）
rm frontend/src/hooks/useWebSocketDiscussion.ts             # WebSocket Hook（未使用）

# API統合
# websocket_discussions.py の機能を discussions.py に統合するか判断
```

## リファクタリング後のメリット

### 1. コード削減
- **Before**: ~500行の重複コード
- **After**: ~200行の統合コード
- **削減率**: 60%削減

### 2. 保守性向上
- 議論メッセージの変更: 4箇所 → 1箇所
- 新機能追加: 複数ファイル → 単一ファイル
- バグ修正: 重複箇所の同期不要

### 3. 機能の明確化
- 通常実行: `run_discussion(discussion, characters, world)`
- ストリーミング: `run_discussion(discussion, characters, world, stream_callback)`
- 単一のAPIで全機能をカバー

## 移行戦略

### 段階的実装（下位互換性保持）
```python
# 1. 新しい統合メソッドを作成
async def run_discussion_unified(self, ...):
    # 統合ロジック

# 2. 既存メソッドを内部で統合メソッドを呼ぶように変更
async def run_discussion(self, ...):
    return await self.run_discussion_unified(...)

async def run_discussion_with_streaming(self, ...):
    return await self.run_discussion_unified(..., stream_callback=stream_data.update)

# 3. 十分テスト後、統合メソッドに置き換え
```

### テスト方針
```python
# 統合前後で同じ結果が得られることを確認
class TestDiscussionIntegration:
    async def test_normal_discussion_compatibility(self):
        # 通常実行が統合前と同じ結果を返すことを確認
        
    async def test_streaming_discussion_compatibility(self):
        # ストリーミング実行が統合前と同じ結果を返すことを確認
        
    async def test_error_handling_consistency(self):
        # エラーハンドリングが一貫していることを確認
```

## 実装優先度

| 項目 | 優先度 | 工数 | 効果 |
|------|--------|------|------|
| システムメッセージ統合 | 🔴 高 | 30分 | 即座の重複解消 |
| 議論生成メソッド統合 | 🟡 中 | 2時間 | 大幅な保守性向上 |
| 未使用ファイル整理 | 🟢 低 | 1時間 | コードベース簡素化 |
| API統合 | 🟢 低 | 4時間 | アーキテクチャ改善 |

**推奨**: Phase 1から段階的に実装し、各段階でテストを実施