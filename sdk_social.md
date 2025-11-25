# DiscordのOauth2からフレンドを読む方法

# ステップ1
sdk.social_layer_presenceをoauth2のスコープにして認証する

# ステップ2
```
https://discord.com/api/v10/users/@me/relationships
```
このURLに、取得できたOauth2TokenをheaderにつけてGetする。

# ステップ3
フレンドリストが取得できる。

# 注意点
これは規約違反かもしれないので、完全に自己責任でお願いします。