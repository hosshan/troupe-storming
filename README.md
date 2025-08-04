# TinyTroupe Brainstorming Application

TinyTroupeと連携したブレインストーミングアプリケーションです。世界を作成し、キャラクターを登録して、テーマに基づいた議論をシミュレーションできます。

| Words | Discussions | Discus |
|:----:|:----:|:----:|
| <img width="1511" height="823" alt="スクリーンショット 2025-08-04 22 55 44" src="https://github.com/user-attachments/assets/2e621e05-1724-4a90-93ef-ad7fb6807999" /> | <img width="1512" height="823" alt="スクリーンショット 2025-08-04 22 55 53" src="https://github.com/user-attachments/assets/90771348-f765-44df-94b7-8015be5de548" /> | <img width="1512" height="823" alt="スクリーンショット 2025-08-04 22 56 08" src="https://github.com/user-attachments/assets/5084808c-112b-451b-ad1f-490405bdefe2" /> |

## 機能

- **世界管理**: 議論の舞台となる世界の作成・編集・削除
- **キャラクター管理**: 各世界にキャラクターを登録・編集・削除
- **議論シミュレーション**: TinyTroupeを使用したキャラクター間の議論
- **結果表示**: 議論の結果を確認

## 技術スタック

### Backend
- Python 3.8+
- FastAPI
- SQLAlchemy (SQLite)
- TinyTroupe

### Frontend
- TypeScript
- React 18
- Shadcn/UI
- Axios

## セットアップ

### Backend

1. バックエンドディレクトリに移動
```bash
cd backend
```

2. 仮想環境を作成・有効化
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 依存関係をインストール
```bash
pip install -r requirements.txt
```

4. **環境変数の設定 (重要)**

OpenAI APIキーを設定してください：

**方法1: .envファイルを使用 (推奨)**
```bash
# backend/.env ファイルを作成
echo "OPENAI_API_KEY=your-actual-openai-api-key-here" > .env
```

**方法2: 環境変数を直接設定**
```bash
export OPENAI_API_KEY="your-actual-openai-api-key-here"
```

⚠️ **注意**: OpenAI APIキーがない場合、TinyTroupeの実際のAI議論機能は使用できず、モックデータが返されます。

5. サーバーを起動
```bash
python main.py
# または
uvicorn main:app --reload --port 8000
```

バックエンドAPI: http://localhost:8000

### Frontend

1. フロントエンドディレクトリに移動
```bash
cd frontend
```

2. 依存関係をインストール
```bash
npm install
```

3. 開発サーバーを起動
```bash
npm start
```

フロントエンド: http://localhost:3000

## 停止処理

### バックエンドの停止

**方法1: 停止スクリプトを使用 (推奨)**
```bash
# プロジェクトルートディレクトリから実行
./stop_backend.sh
```

**方法2: 手動でプロセスを停止**
```bash
# プロセスを確認
ps aux | grep -E "(uvicorn|python.*app|python.*main)" | grep -v grep

# プロセスを停止
pkill -f "uvicorn.*app.main:app"
pkill -f "python.*main.py"
pkill -f "python.*-m uvicorn"

# 強制停止（必要に応じて）
pkill -9 -f "uvicorn.*app.main:app"
pkill -9 -f "python.*main.py"
```

**方法3: Ctrl+C (ターミナルで実行中の場合)**
```bash
# バックエンドサーバーが実行中のターミナルで
Ctrl+C
```

### フロントエンドの停止

**方法1: Ctrl+C (ターミナルで実行中の場合)**
```bash
# フロントエンドサーバーが実行中のターミナルで
Ctrl+C
```

**方法2: プロセスを直接停止**
```bash
pkill -f "react-scripts start"
pkill -f "npm start"
```

### 全プロセスの一括停止

```bash
# バックエンドとフロントエンドの両方を停止
./stop_backend.sh
pkill -f "react-scripts start"
pkill -f "npm start"
```

### トラブルシューティング

**プロセスが停止しない場合:**
```bash
# プロセスIDを確認
ps aux | grep -E "(uvicorn|python.*app|python.*main|react-scripts)" | grep -v grep

# 特定のプロセスIDを強制停止
kill -9 <プロセスID>
```

**ポートが使用中の場合:**
```bash
# ポート8000を使用しているプロセスを確認
lsof -i :8000

# ポート3000を使用しているプロセスを確認
lsof -i :3000

# 特定のポートを使用しているプロセスを停止
kill -9 $(lsof -t -i:8000)
kill -9 $(lsof -t -i:3000)
```

## 使用方法

1. **世界作成**: まず議論の舞台となる世界を作成します
2. **キャラクター登録**: 作成した世界にキャラクターを追加します
3. **議論テーマ投稿**: 議論したいテーマを投稿します
4. **議論開始**: TinyTroupeを使用してキャラクター間の議論を開始します
5. **結果確認**: 議論の結果を確認します

## APIエンドポイント

### 世界管理
- `GET /api/worlds` - 世界一覧取得
- `POST /api/worlds` - 世界作成
- `GET /api/worlds/{id}` - 世界詳細取得
- `PUT /api/worlds/{id}` - 世界更新
- `DELETE /api/worlds/{id}` - 世界削除

### キャラクター管理
- `GET /api/characters` - キャラクター一覧取得
- `POST /api/characters` - キャラクター作成
- `GET /api/characters/{id}` - キャラクター詳細取得
- `PUT /api/characters/{id}` - キャラクター更新
- `DELETE /api/characters/{id}` - キャラクター削除

### 議論管理
- `GET /api/discussions` - 議論一覧取得
- `POST /api/discussions` - 議論作成
- `GET /api/discussions/{id}` - 議論詳細取得
- `POST /api/discussions/{id}/start` - 議論開始
- `PUT /api/discussions/{id}` - 議論更新

## プロジェクト構造

```
troupe-storming/
├── backend/
│   ├── app/
│   │   ├── api/           # APIエンドポイント
│   │   ├── database/      # データベース設定
│   │   ├── models/        # データモデル
│   │   └── services/      # ビジネスロジック
│   ├── main.py           # FastAPIアプリケーション
│   └── requirements.txt  # Python依存関係
├── frontend/
│   ├── src/
│   │   ├── components/   # Reactコンポーネント
│   │   ├── pages/        # ページコンポーネント
│   │   ├── services/     # API呼び出し
│   │   └── types/        # TypeScript型定義
│   ├── package.json      # Node.js依存関係
│   └── tsconfig.json     # TypeScript設定
└── stop_backend.sh       # バックエンド停止スクリプト
```

## 開発

### Backend開発
- FastAPIの自動生成ドキュメント: http://localhost:8000/docs
- データベースファイル: `troupe_storming.db` (SQLite)

### Frontend開発
- React DevTools推奨
- Material-UIコンポーネントを使用

## TinyTroupe設定詳細

### OpenAI APIキーの取得方法

1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
2. アカウントにログインまたは新規登録
3. "Create new secret key" をクリック
4. 生成されたAPIキーを `.env` ファイルに設定

### TinyTroupe設定

現在の設定では以下のOpenAIモデルを使用：
- **メインモデル**: `gpt-4.1-mini`
- **推論モデル**: `o3-mini`  
- **埋め込みモデル**: `text-embedding-3-small`

### 動作確認方法

1. バックエンドサーバー起動後、以下にアクセス:
   - API文書: http://localhost:8000/docs
   - ヘルスチェック: http://localhost:8000/health

2. フロントエンド起動後:
   - 世界を作成
   - キャラクターを追加（最低2人）
   - 議論テーマを作成
   - 「議論開始」ボタンをクリック
   - 結果を確認

### トラブルシューティング

**TinyTroupeが動作しない場合:**
- OpenAI APIキーが正しく設定されているか確認
- APIキーの有効性と残高を確認
- ログで `TinyTroupe successfully imported` が表示されるか確認

**モックデータが表示される場合:**
- `.env` ファイルが `backend/` ディレクトリにあるか確認
- APIキーに余分なスペースや引用符がないか確認

**WebSocket処理中の問題:**
- 画面リロード時にEventSource接続が適切にクリーンアップされるよう修正済み
- プロセス停止スクリプト `stop_backend.sh` を使用して安全に停止
- タイムアウト処理により無限ループを防止

## 注意事項

- **APIコスト**: TinyTroupeはOpenAI APIを使用するため、使用量に応じて料金が発生します
- **レート制限**: OpenAI APIのレート制限にご注意ください
- **データベース**: SQLiteファイル (`troupe_storming.db`) は自動生成されます
- **本番環境では環境変数による設定管理を推奨**
- **プロセス停止**: 必ず適切な停止処理を使用し、強制終了は避けてください
