# TinyTroupe Brainstorming Application

TinyTroupeと連携したブレインストーミングアプリケーションです。世界を作成し、キャラクターを登録して、テーマに基づいた議論をシミュレーションできます。

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
- Material-UI
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
└── frontend/
    ├── src/
    │   ├── components/   # Reactコンポーネント
    │   ├── pages/        # ページコンポーネント
    │   ├── services/     # API呼び出し
    │   └── types/        # TypeScript型定義
    ├── package.json      # Node.js依存関係
    └── tsconfig.json     # TypeScript設定
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

## 注意事項

- **APIコスト**: TinyTroupeはOpenAI APIを使用するため、使用量に応じて料金が発生します
- **レート制限**: OpenAI APIのレート制限にご注意ください
- **データベース**: SQLiteファイル (`troupe_storming.db`) は自動生成されます
- **本番環境では環境変数による設定管理を推奨**