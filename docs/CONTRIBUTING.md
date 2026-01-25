# 貢献ガイドライン

このドキュメントでは SharkBot-v2 への貢献方法について説明します。

## 目次

- [はじめに](#はじめに)
- [行動規範](#行動規範)
- [貢献の種類](#貢献の種類)
- [開発フロー](#開発フロー)
- [コーディング規約](#コーディング規約)
- [コミット規約](#コミット規約)
- [プルリクエスト](#プルリクエスト)
- [Issue の作成](#issue-の作成)

## はじめに

SharkBot-v2 への貢献に興味を持っていただきありがとうございます！このプロジェクトはコミュニティの協力によって成長しています。

### 貢献する前に

1. [README.md](../README.md) を読む
2. [DEVELOPER.md](./DEVELOPER.md) で開発の基本を理解する
3. [SETUP.md](./SETUP.md) で開発環境をセットアップする
4. 既存の Issue や Pull Request を確認する

## 行動規範

[CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) を遵守してください。

基本原則:
- 敬意を持って接する
- 建設的なフィードバックを提供する
- 多様性を尊重する
- ハラスメントを行わない

## 貢献の種類

### 1. バグ報告

バグを見つけた場合は Issue を作成してください。

**含めるべき情報**:
- バグの詳細な説明
- 再現手順
- 期待される動作
- 実際の動作
- 環境情報 (OS, Python バージョンなど)
- スクリーンショット (該当する場合)

### 2. 機能提案

新しい機能を提案する場合は Issue を作成してください。

**含めるべき情報**:
- 機能の詳細な説明
- なぜその機能が必要か
- 使用例
- 代替案 (該当する場合)

### 3. ドキュメント改善

ドキュメントの誤字脱字、不明確な説明、追加すべき内容などがあれば、Issue を作成するか Pull Request を送ってください。

### 4. コード貢献

新機能の追加やバグ修正のコードを貢献してください。

## 開発フロー

### 1. リポジトリをフォーク

GitHub でリポジトリをフォークします。

### 2. ブランチを作成

```bash
git clone https://github.com/YOUR-USERNAME/SharkBot-v2.git
cd SharkBot-v2
git checkout -b feature/my-new-feature
```

ブランチ命名規則:
- `feature/機能名`: 新機能
- `fix/バグ名`: バグ修正
- `docs/ドキュメント名`: ドキュメント更新
- `refactor/リファクタリング名`: リファクタリング

### 3. 変更を加える

コードを変更し、テストを追加します。

```bash
# 開発環境のセットアップ
cd src
pip install -r requirements.txt

# コードを編集
# ...

# テストを実行
python test_bot.py
```

### 4. コミット

```bash
git add .
git commit -m "Add: 新しい機能を追加"
```

### 5. プッシュ

```bash
git push origin feature/my-new-feature
```

### 6. Pull Request を作成

GitHub でフォークしたリポジトリから Pull Request を作成します。

## コーディング規約

### Python スタイル

- **PEP 8** に準拠
- **型ヒント** を使用 (可能な限り)
- **docstring** を記述 (重要な関数やクラス)

#### 例

```python
from typing import Optional
import discord
from discord.ext import commands

class MyCog(commands.Cog):
    """
    説明: このCogの機能
    """
    
    def __init__(self, bot: commands.Bot) -> None:
        """
        Args:
            bot: Botインスタンス
        """
        self.bot = bot
    
    async def my_function(self, user_id: int) -> Optional[dict]:
        """
        ユーザーデータを取得します。
        
        Args:
            user_id: ユーザーID
            
        Returns:
            ユーザーデータ、または None
        """
        db = self.bot.async_db["Main"]
        return await db.find_one({"User": user_id})
```

### フォーマッター

コードを自動整形してください:

```bash
# autopep8 を使用
autopep8 --in-place --recursive src/

# または ruff を使用
ruff format src/
```

### リンター

コードをチェックしてください:

```bash
# flake8 を使用
flake8 src/

# または ruff を使用
ruff check src/
```

### pre-commit

pre-commit フックを使用すると、コミット前に自動的にチェックされます:

```bash
pip install pre-commit
pre-commit install
```

### 命名規則

- **変数・関数**: `snake_case`
- **クラス**: `PascalCase`
- **定数**: `UPPER_CASE`
- **プライベート**: `_leading_underscore`

#### 例

```python
# 良い例
class UserManager:
    MAX_USERS = 100
    
    def __init__(self):
        self.user_count = 0
        self._cache = {}
    
    def add_user(self, user_id: int) -> None:
        pass

# 悪い例
class userManager:
    maxUsers = 100
    
    def __init__(self):
        self.UserCount = 0
    
    def AddUser(self, userId: int) -> None:
        pass
```

## コミット規約

### コミットメッセージのフォーマット

```
[種類]: 変更内容の簡潔な説明

詳細な説明 (オプション)

関連Issue: #123
```

### 種類

- `Add`: 新機能追加
- `Fix`: バグ修正
- `Update`: 既存機能の更新
- `Remove`: 機能の削除
- `Refactor`: リファクタリング
- `Docs`: ドキュメント更新
- `Style`: コードスタイルの変更 (機能に影響なし)
- `Test`: テストの追加・修正
- `Chore`: ビルドプロセスやツールの変更

### 例

```
Add: 投票コマンドを追加

/poll コマンドで簡単に投票を作成できるようになりました。
最大4つの選択肢をサポートしています。

関連Issue: #42
```

```
Fix: ロールパネルの表示バグを修正

ロールが多い場合に正しく表示されない問題を修正しました。

関連Issue: #123
```

## プルリクエスト

### PR の作成

1. フォークしたリポジトリからオリジナルリポジトリに PR を作成
2. タイトルに変更内容を簡潔に記載
3. 説明に以下を含める:
   - 変更内容の詳細
   - 変更理由
   - テスト方法
   - スクリーンショット (UI変更の場合)
   - 関連 Issue

### PR テンプレート

```markdown
## 変更内容
<!-- 何を変更したか -->

## 変更理由
<!-- なぜ変更したか -->

## テスト方法
<!-- どのようにテストしたか -->

## スクリーンショット
<!-- UI変更がある場合 -->

## チェックリスト
- [ ] コードが正しく動作することを確認した
- [ ] 既存のテストが通ることを確認した
- [ ] 新しいテストを追加した (該当する場合)
- [ ] ドキュメントを更新した (該当する場合)
- [ ] コーディング規約に従っている
- [ ] コミットメッセージが規約に従っている

## 関連 Issue
<!-- 関連する Issue があれば記載 -->
Closes #123
```

### レビュープロセス

1. メンテナーが PR をレビュー
2. 修正が必要な場合はコメント
3. 修正を行い、再度プッシュ
4. 承認されたらマージ

### PR のガイドライン

- **小さく保つ**: 1つの PR で1つの機能または修正
- **テストを含める**: 新機能にはテストを追加
- **ドキュメントを更新**: 必要に応じてドキュメントも更新
- **コンフリクトを解決**: マージ前にコンフリクトを解決
- **CI をパス**: すべてのチェックが通ることを確認

## Issue の作成

### バグ報告テンプレート

```markdown
## バグの説明
<!-- バグの詳細な説明 -->

## 再現手順
1. 
2. 
3. 

## 期待される動作
<!-- 何が起こるべきか -->

## 実際の動作
<!-- 実際に何が起こったか -->

## 環境
- OS: 
- Python バージョン: 
- discord.py バージョン: 

## スクリーンショット
<!-- 該当する場合 -->

## 追加情報
<!-- その他の情報 -->
```

### 機能提案テンプレート

```markdown
## 機能の説明
<!-- 提案する機能の詳細な説明 -->

## 必要性
<!-- なぜその機能が必要か -->

## 使用例
<!-- どのように使用するか -->

## 代替案
<!-- 他に考えられる方法 -->

## 追加情報
<!-- その他の情報 -->
```

## テスト

### テストの実行

```bash
cd src
python test_bot.py
```

### テストの作成

新機能にはテストを追加してください:

```python
import unittest
from my_cog import MyCog

class TestMyCog(unittest.TestCase):
    def setUp(self):
        # テストの準備
        pass
    
    def test_my_function(self):
        # テストコード
        result = my_function()
        self.assertEqual(result, expected_value)
    
    def tearDown(self):
        # テストの後処理
        pass

if __name__ == '__main__':
    unittest.main()
```

## コミュニティ

### コミュニケーション

- **GitHub Issues**: バグ報告、機能提案
- **GitHub Discussions**: 質問、ディスカッション
- **Pull Requests**: コードレビュー、議論

### サポート

質問や問題がある場合:
1. [ドキュメント](./DEVELOPER.md) を確認
2. 既存の Issue を検索
3. 新しい Issue を作成

## ライセンス

貢献したコードは GPL-3.0 ライセンスの下で公開されます。

## 謝辞

SharkBot-v2 への貢献ありがとうございます！あなたの貢献がプロジェクトをより良くします。

## 参考資料

- [Python コーディング規約 (PEP 8)](https://peps.python.org/pep-0008/)
- [discord.py ドキュメント](https://discordpy.readthedocs.io/)
- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)
- [MongoDB ドキュメント](https://docs.mongodb.com/)
