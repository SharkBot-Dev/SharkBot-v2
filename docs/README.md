# SharkBot-v2 ドキュメント

SharkBot-v2 の開発者向けドキュメント集へようこそ！

## 📚 ドキュメント一覧

### 開発者向けドキュメント

| ドキュメント | 説明 |
|------------|------|
| [DEVELOPER.md](./DEVELOPER.md) | 開発者ガイド - プロジェクト概要、技術スタック、基本的な開発方法 |
| [SETUP.md](./SETUP.md) | 開発環境のセットアップガイド - インストール手順、設定方法 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | システムアーキテクチャ - Bot の内部構造、データベース設計 |
| [COG_DEVELOPMENT.md](./COG_DEVELOPMENT.md) | Cog 開発ガイド - コマンドの作成方法、ベストプラクティス |
| [API.md](./API.md) | API ドキュメント - Web API、ダッシュボードの使用方法 |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | 貢献ガイドライン - コード貢献の方法、規約 |
| [DevHelp.md](./DevHelp.md) | 開発者向けヘルプ - よくある質問、Tips |

### ユーザー向けドキュメント

| ドキュメント | 説明 |
|------------|------|
| [START.md](./START.md) | Bot の使い方 - ユーザー向けスタートガイド |
| [Main/](./Main/) | 主要機能の説明 - 各機能の詳細なドキュメント |

## 🚀 クイックスタート

### 1. 初めて開発する場合

```
[README.md (ルート)] → [DEVELOPER.md] → [SETUP.md]
     ↓
開発環境のセットアップ完了
     ↓
[COG_DEVELOPMENT.md] or [API.md]
```

### 2. コードを理解したい場合

```
[ARCHITECTURE.md] → [DEVELOPER.md] → [COG_DEVELOPMENT.md]
```

### 3. 貢献したい場合

```
[CONTRIBUTING.md] → [SETUP.md] → [DEVELOPER.md]
```

## 📖 ドキュメント詳細

### DEVELOPER.md
開発者向けの総合ガイドです。SharkBot-v2 の全体像を把握するために最初に読むべきドキュメントです。

**内容**:
- プロジェクト概要
- 技術スタック
- プロジェクト構成
- コーディング規約
- 関連ドキュメントへのリンク

**対象読者**: すべての開発者

### SETUP.md
開発環境をセットアップするための詳細なガイドです。

**内容**:
- 必要な環境
- インストール手順
- 設定方法
- Bot の起動方法
- トラブルシューティング

**対象読者**: 新規開発者、環境構築が必要な開発者

### ARCHITECTURE.md
SharkBot-v2 のシステムアーキテクチャを詳しく説明します。

**内容**:
- 全体構成
- Bot アーキテクチャ
- データベース設計
- Web ダッシュボード
- マイクロサービス
- フロー図

**対象読者**: システム全体を理解したい開発者、アーキテクチャに興味がある開発者

### COG_DEVELOPMENT.md
Cog (Bot のコマンド機能) を開発するための包括的なガイドです。

**内容**:
- Cog の基本
- コマンドの種類
- データベースの使用
- エラーハンドリング
- 権限チェック
- 翻訳対応
- 実例とサンプルコード

**対象読者**: Bot のコマンド機能を開発する開発者

### API.md
Web API とダッシュボードの開発ガイドです。

**内容**:
- API 概要
- 認証システム
- エンドポイント一覧
- ダッシュボード開発
- API の拡張方法
- セキュリティ

**対象読者**: Web API やダッシュボードを開発する開発者

### CONTRIBUTING.md
プロジェクトへの貢献方法をまとめたガイドラインです。

**内容**:
- 貢献の種類
- 開発フロー
- コーディング規約
- コミット規約
- プルリクエストの作成方法
- Issue の作成方法

**対象読者**: プロジェクトに貢献したいすべての人

## 🎯 用途別ドキュメント

### 新機能を追加したい

1. [DEVELOPER.md](./DEVELOPER.md) でプロジェクト構成を理解
2. [COG_DEVELOPMENT.md](./COG_DEVELOPMENT.md) または [API.md](./API.md) で開発方法を学ぶ
3. [CONTRIBUTING.md](./CONTRIBUTING.md) で貢献方法を確認

### バグを修正したい

1. [ARCHITECTURE.md](./ARCHITECTURE.md) でシステムを理解
2. [DEVELOPER.md](./DEVELOPER.md) でコーディング規約を確認
3. [CONTRIBUTING.md](./CONTRIBUTING.md) でプルリクエストの作成方法を確認

### システムを理解したい

1. [DEVELOPER.md](./DEVELOPER.md) で全体像を把握
2. [ARCHITECTURE.md](./ARCHITECTURE.md) で詳細なアーキテクチャを学ぶ
3. [COG_DEVELOPMENT.md](./COG_DEVELOPMENT.md) と [API.md](./API.md) で具体的な実装を理解

### ドキュメントを改善したい

1. [CONTRIBUTING.md](./CONTRIBUTING.md) で貢献方法を確認
2. 既存のドキュメントを読んで改善点を見つける
3. Issue または Pull Request を作成

## 🔧 技術スタック

### メイン技術
- **Python 3.11+**: プログラミング言語
- **discord.py 2.6.4**: Discord Bot フレームワーク
- **MongoDB**: データベース
- **FastAPI**: Web API フレームワーク

### 主要ライブラリ
- motor: MongoDB 非同期ドライバ
- pymongo: MongoDB 同期ドライバ
- jishaku: Bot デバッグツール
- aiohttp: 非同期 HTTP クライアント
- Pillow: 画像処理
- matplotlib: グラフ生成

詳細は [DEVELOPER.md](./DEVELOPER.md) を参照してください。

## 📝 コーディング規約

### Python スタイル
- PEP 8 に準拠
- 型ヒントを使用
- autopep8 または ruff でコードを整形

### コミットメッセージ
```
[種類]: 変更内容の説明

詳細な説明 (オプション)
```

種類: `Add`, `Fix`, `Update`, `Remove`, `Refactor`, `Docs`, `Style`, `Test`, `Chore`

詳細は [CONTRIBUTING.md](./CONTRIBUTING.md) を参照してください。

## 🤝 コミュニティ

### サポート
- **GitHub Issues**: バグ報告、機能提案
- **GitHub Discussions**: 質問、ディスカッション
- **Pull Requests**: コード貢献

### 貢献方法
1. リポジトリをフォーク
2. ブランチを作成
3. 変更を加える
4. テストを実行
5. プルリクエストを作成

詳細は [CONTRIBUTING.md](./CONTRIBUTING.md) を参照してください。

## 📚 参考資料

### 公式ドキュメント
- [discord.py ドキュメント](https://discordpy.readthedocs.io/)
- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)
- [MongoDB ドキュメント](https://docs.mongodb.com/)
- [Python ドキュメント](https://docs.python.org/3/)

### ガイド
- [PEP 8 - Python コーディング規約](https://peps.python.org/pep-0008/)
- [Discord Developer Portal](https://discord.com/developers/docs)

## 📌 よくある質問

### Q: どこから始めればいいですか？
A: まず [README.md](../README.md) を読み、次に [DEVELOPER.md](./DEVELOPER.md) を読んでください。その後、[SETUP.md](./SETUP.md) に従って開発環境をセットアップしてください。

### Q: Cog の作成方法を知りたいです。
A: [COG_DEVELOPMENT.md](./COG_DEVELOPMENT.md) に詳しい説明があります。

### Q: ダッシュボードの開発方法を知りたいです。
A: [API.md](./API.md) に詳しい説明があります。

### Q: バグを見つけました。どうすればいいですか？
A: [CONTRIBUTING.md](./CONTRIBUTING.md) の「バグ報告」セクションを参照して、GitHub Issues で報告してください。

### Q: 新機能を提案したいです。
A: [CONTRIBUTING.md](./CONTRIBUTING.md) の「機能提案」セクションを参照して、GitHub Issues で提案してください。

## 📄 ライセンス

このプロジェクトは GPL-3.0 ライセンスの下で公開されています。詳細は [LICENSE](../LICENSE) を参照してください。

## 🙏 謝辞

SharkBot-v2 の開発に貢献してくださったすべての方に感謝します！

---

**Note**: ドキュメントに間違いや不明瞭な点がある場合は、Issue を作成するか Pull Request を送ってください。
