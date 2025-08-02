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

4. サーバーを起動
```bash
python main.py
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

## 注意事項

- TinyTroupeの実際の統合はサンプル実装です
- 本番環境では環境変数による設定管理を推奨
- データベースのマイグレーション機能は未実装