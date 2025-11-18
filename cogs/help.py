from discord.ext import commands
import discord
from consts import settings
from discord import app_commands
from models import command_disable, make_embed

HELP_TREE = {
    "管理機能": {
        "モデレーション": [
            {"name": "moderation kick", "description": "メンバーをキックします。"},
            {"name": "moderation ban ban", "description": "ユーザーをBanします。"},
            {"name": "moderation ban unban", "description": "ユーザーのBanを解除します。"},
            {"name": "moderation ban massban", "description": "複数人を一斉にbanします。"},
            {"name": "moderation ban softban", "description": "Ban機能を利用してメッセージを一斉削除します。"},
            {"name": "moderation timeout", "description": "メンバーをタイムアウトします。"},
            {"name": "moderation untimeout", "description": "タイムアウトを解除します。"},
            {"name": "moderation max-timeout", "description": "タイムアウトができる最大までタイムアウトします。"},
            {"name": "moderation clear", "description": "メッセージを削除します。"},
            {"name": "moderation warn", "description": "メンバーを警告します。"},
            {"name": "moderation warns", "description": "メンバーの警告回数を確認します。"},
            {"name": "moderation remake", "description": "チャンネルを再生成します。"},
            {"name": "moderation lock", "description": "チャンネルで話せなくします。"},
            {"name": "moderation unlock", "description": "チャンネルを開放します。"},
            {"name": "moderation report", "description": "通報チャンネルをセットアップします。"},
            {"name": "moderation serverban", "description": "web認証時に指定したサーバーに入っていると認証できなくします。"},
            {"name": "moderation serverunban", "description": "web認証時に指定したサーバーに入っていても認証できるようにします。"},
            {"name": "moderation auditlog", "description": "監査ログをダンプします。"},
            {"name": "moderation lottery", "description": "抽選をします。"},
        ],
        "DM・招待停止": [
            {"name": "moderation pause invite", "description": "招待を一時停止します。"},
            {"name": "moderation pause dm", "description": "DMを一時停止します。"},
            {"name": "moderation pause both", "description": "DMと招待を一時停止します。"},
        ],
        "自動管理": [
            {"name": "automod create", "description": "AutoModを作成します。"},
            {"name": "automod delete", "description": "AutoModを削除します。"},
            {"name": "automod customword", "description": "カスタムワードを禁止するAutoModを作成します。"},
        ],
        "自動返信": [
            {"name": "autoreply create", "description": "自動返信を作成します。"},
            {"name": "autoreply delete", "description": "自動返信を削除します。"},
            {"name": "autoreply list", "description": "自動返信リストを表示します。"},
            {"name": "autoreply templates", "description": "自動返信をテンプレートから作成します。"},
            {"name": "autoreply export", "description": "自動返信ををエクスポートします。"},
            {"name": "autoreply import", "description": "自動返信ををインポートします。"},
        ],
        "自動リアクション": [
            {"name": "autoreact channel", "description": "自動リアクションをチャンネルを条件にして作成します。"},
            {"name": "autoreact word", "description": "自動リアクションをワードを条件にして作成します。"},
            {"name": "autoreact remove", "description": "自動リアクションを削除します。"},
            {"name": "autoreact list", "description": "自動リアクションをリスト化します。"}
        ],
        "自動GIF・GIF検索": [
            {"name": "gif search", "description": "GIFを検索します。"},
            {"name": "gif autogif-channel add", "description": "自動gif返信のチャンネルを追加します。"},
            {"name": "gif autogif-channel remove", "description": "自動gif返信チャンネルを削除します。"},
        ],
        "オフライン検知": [
            {"name": "autodown settings", "description": "オフライン検知の設定を確認します。"},
            {"name": "autodown vc-kick", "description": "オフラインになるとVCからキックするように設定します。"},
        ],
        "ロール管理": [
            {"name": "role add", "description": "ロールを追加します。"},
            {"name": "role remove", "description": "ロールを剝奪します。"},
            {"name": "role color-role", "description": "色ロールを作成します。"},
            {"name": "role can-bot", "description": "そのロールをBotが扱えるかをチェックします。"},
        ],
        "ニックネーム管理": [
            {"name": "nick edit", "description": "ニックネームを編集します。"},
            {"name": "role reset", "description": "ニックネームをリセットします。"},
        ],
        "VC管理": [
            {"name": "vc move", "description": "VCにメンバーを移動させます。"},
            {"name": "vc leave", "description": "VCからメンバーを退出させます。"},
            {"name": "vc bomb", "description": "VCを解散させます。"},
            {"name": "vc gather", "description": "一つのVCに集めます。"},
            {"name": "vc temp", "description": "一時的なVCを作成できるチャンネルを作成します。"},
            {"name": "vc alert", "description": "VCのアラートを作成します。"},
        ],
        "様々なパネル": {
            "ロールパネル": [
                {"name": "panel role", "description": "ロールパネルを作成します。"},
                {"name": "panel role-edit", "description": "ロールパネルを編集します。"},
                {"name": "panel newgui-rolepanel", "description": "新しいロールパネルを作成します。"},
                {"name": "panel newgui-rolepanel-edit", "description": "新しいロールパネルを編集します。"},
                {"name": "panel select-rolepanel", "description": "セレクトボックス式ロールパネルを作成します。"},
                {"name": "panel random", "description": "ランダムなロールが付与されるロールパネルを作成します。"},
            ],
            "アンケート・メンバー募集": [
                {"name": "panel poll", "description": "投票ををします。"},
                {"name": "panel enquete", "description": "アンケートを取ります。"},
                {"name": "panel party", "description": "募集パネルを作成します。"},
            ],
            "チケット": [
                {"name": "panel ticket", "description": "チケットパネルを作成します。"},
            ],
            "認証": [
                {"name": "panel auth abs-auth", "description": "絶対値を入力させる認証パネルを作成します。"},
                {"name": "panel auth arror-auth", "description": "矢印の向きを入力させるパネルを作成します。"},
                {"name": "panel auth auth", "description": "ワンクリック認証パネルを作成します。"},
                {"name": "panel auth-plus", "description": "認証したらロールが外れた後にロールが付くパネルを作ります。"},
                {"name": "panel auth webauth", "description": "Web認証パネルを作成します。"},
                {"name": "panel auth image", "description": "画像認証パネルを作成します。"},
                {"name": "panel auth guideline", "description": "ルールに同意させるパネルを作成します。"},
                {"name": "panel auth auth-reqrole", "description": "認証パネルに必要なロールを設定します。"},
            ]
        },
        "グローバルチャット": [
            {"name": "global join", "description": "グローバルチャットに参加します。"},
            {"name": "global leave", "description": "グローバルチャットから退出します。"},
            {"name": "global ads", "description": "グローバル宣伝に参加します。"},
            {"name": "global sgc", "description": "スーパーグローバルチャットに参加します。"},
            {"name": "global sgc-info", "description": "スーパーグローバルチャットの情報を取得します。"},
        ],
        "レベル・実績": {
            "レベル": [
                {"name": "level setting", "description": "レベルを有効化します。"},
                {"name": "level show", "description": "現在のレベルを表示します。"},
                {"name": "level card-custom", "description": "レベルカードをカスタマイズします。"},
                {"name": "level card", "description": "レベルカードを作成します。"},
                {"name": "level channel", "description": "レベルアップ通知を設定します。"},
                {"name": "level role", "description": "レベルアップ時の付与するロールを設定します。"},
                {"name": "level message", "description": "レベルアップ時に送信するメッセージを修正します。"},
                {"name": "level edit", "description": "レベルを編集します。"},
                {"name": "level timing", "description": "レベルアップするタイミングを設定します。"},
                {"name": "level rewards", "description": "レベルアップ時の報酬を取得します。"},
                {"name": "level ranking", "description": "レベルランキングを取得します。"},
                {"name": "level reset", "description": "レベルをリセットします。"},
            ],
            "実績": [
                {"name": "achievement setting", "description": "実績を有効化します。"},
                {"name": "achievement show", "description": "達成した・達成可能な実績一覧を表示します。"},
                {"name": "achievement create", "description": "実績を作成します。"},
                {"name": "achievement delete", "description": "実績を削除します。"},
                {"name": "achievement channel", "description": "実績の通知をするチャンネルをセットアップします。"},
                {"name": "achievement reset", "description": "実績をリセットします。"}
            ]
        },
        "Give a way": [
            {"name": "giveaway create", "description": "サーバー内でのプレゼント企画を実施します。"}
        ],
        "サーバー掲示板": [
            {"name": "global register", "description": "サーバー掲示板に登録します。"},
            {"name": "global server", "description": "サーバー掲示板のURLを取得します。"},
            {"name": "global up", "description": "サーバー掲示板でUPをします。"},
        ],
        "様々なアラート": [
            {"name": "alert news", "description": "ニュースを通知するチャンネルをセットアップします。"},
            {"name": "alert event", "description": "イベント作成を通知するチャンネルをセットアップします。"},
            {"name": "alert mention", "description": "通知時に一緒に送るメンションを指定します。"},
        ],
        "その他設定": [
            {"name": "settings lock-message", "description": "固定メッセージをセットアップします。"},
            {"name": "settings prefix", "description": "頭文字を設定します。"},
            {"name": "settings score", "description": "処罰スコアを設定します。"},
            {"name": "settings warn-setting", "description": "AutoModでの警告時に実行する内容を設定します。"},
            {"name": "settings expand", "description": "メッセージ展開をセットアップします。"},
            {"name": "settings auto-publish", "description": "自動アナウンス公開をセットアップします。"},
            {"name": "settings file-deletor", "description": "自動的に削除するファイル拡張子を設定します。"},
            {"name": "settings auto-translate", "description": "自動翻訳を設定します。"},
            {"name": "settings good-morning", "description": "Botが挨拶をするチャンネルをセットアップします。"},
            {"name": "settings auto-thread", "description": "自動スレッド作成をセットアップします。"},
            {"name": "settings lang", "description": "Change the bot's language. (Beta)"},
        ]
    },
    "便利機能": {
        "ネットワークツール": [
            {"name": "tools network iplookup", "description": "IPを検索します。"},
            {"name": "tools network nslookup", "description": "DNS情報を取得します。"},
            {"name": "tools network meta", "description": "サイトのメタデータを取得します。"},
            {"name": "tools network ping", "description": "ドメインにPingを送信します。"},
            {"name": "tools network whois", "description": "Whois検索をします。"},
        ],
        "計算機能": [
            {"name": "tools calc size-converter", "description": "サイズの計算をします。"},
            {"name": "tools calc calculator", "description": "電卓を使用します。"},
        ],
        "OCR機能": [
            {"name": "tools ocr ocr", "description": "OCRをします・"},
        ],
        "Twitter系の機能": [
            {"name": "tools twitter info", "description": "ツイート情報を取得します。"},
        ],
        "その他便利機能": [
            {"name": "tools embed", "description": "埋め込みを作成します。"},
            {"name": "tools button", "description": "ボタンを作成します。"},
            {"name": "tools choise", "description": "Botが選びます。"},
            {"name": "tools timestamp", "description": "timestampを作成します。"},
            {"name": "tools todo", "description": "TODOを作成します。"},
            {"name": "tools invite", "description": "招待リンクを作成します。"},
            {"name": "tools uuid", "description": "UUIDを作成します。"},
            {"name": "tools short", "description": "短縮URLを作成します。"},
            {"name": "tools afk", "description": "留守番をしてもらいます。"},
            {"name": "tools timer", "description": "タイマーをセットします。"},
            {"name": "tools qr", "description": "QRコードを作成&読み取りします。"},
            {"name": "tools weather", "description": "天気を取得します。"},
            {"name": "tools reminder", "description": "リマインダーを作成します。"},
            {"name": "tools calendar", "description": "カレンダーをダウンロードします。"},
            {"name": "tools download", "description": "いろいろダウンロードします。"},
        ]
    },
    "検索機能": {
        "Discord上の検索": [
            {"name": "search multi", "description": "一斉に検索します。"},
            {"name": "search tag", "description": "サーバータグを何人がつけているかを検索します。"},
            {"name": "search user", "description": "ユーザーを検索します。"},
            {"name": "search server", "description": "サーバーを検索します。"},
            {"name": "search channel", "description": "チャンネルを検索します。"},
            {"name": "search ban", "description": "ユーザーBanを検索します。"},
            {"name": "search bot", "description": "サーバーに入れたBotを検索します。"},
            {"name": "search invite", "description": "招待リンクを検索します。"},
            {"name": "search avatar", "description": "ユーザーのアバターを検索します。"},
            {"name": "search banner", "description": "ユーザーのバナーを検索します。"},
            {"name": "search emoji", "description": "絵文字を検索します。"},
            {"name": "search spotify", "description": "ユーザーの聞いている曲を検索します。"},
            {"name": "search snowflake", "description": "Snowflakeを検索します。"},
        ],
        "Web上の検索": [
            {"name": "search web translate", "description": "翻訳をします。"},
            {"name": "search web news", "description": "ニュースを取得します。"},
            {"name": "search web wikipedia", "description": "Wikipediaを取得します。"},
            {"name": "search web safeweb", "description": "SafeWebでURLの安全性をチェックします。"},
            {"name": "search web anime", "description": "アニメを検索します。"},
        ]
    },
    "面白い機能": {
        "グローバルゲーム": [
            {"name": "game emerald mining", "description": "ゲームをするのに必要なエメラルドを集めます。"},
            {"name": "game emerald slot", "description": "スロットを回します。"},
            {"name": "game emerald info", "description": "自分の情報を取得します。"},
            {"name": "game emerald buy", "description": "エメラルドを使ってアイテムを購入します。"},
        ],
        "グローバルな木": [
            {"name": "tree image", "description": "グローバルな木の写真を撮ります。"},
            {"name": "tree watering", "description": "グローバルな木に水をまきます。"},
            {"name": "tree status", "description": "グローバルな木の情報を取得します。"},
            {"name": "tree mystatus", "description": "自分の育てた木の情報を取得します。"},
        ],
        "ペット育成": [
            {"name": "animal status", "description": "動物のステータスを確認します。"},
            {"name": "animal feed", "description": "動物にエサを与えます。"},
            {"name": "animal keeping", "description": "ペットを新しく飼います。"},
            {"name": "animal train", "description": "ペットを鍛えます。"},
        ],
        "スクラッチ": [
            {"name": "game scratch user", "description": "スクラッチでのユーザーを取得します。"},
            {"name": "game scratch project", "description": "スクラッチのプロジェクトを取得します。"}
        ],
        "Osu": [
            {"name": "game osu user", "description": "Osuのユーザー情報を取得します。"}
        ],
        "ポケモン": [
            {"name": "game pokemon search", "description": "ポケモンを検索します。"}
        ],
        "フォートナイト": [
            {"name": "game fortnite map", "description": "フォートナイトのマップを取得するよ"},
            {"name": "game fortnite player", "description": "フォートナイトのプレイヤーを取得します。"}
        ],
        "Minecraft": [
            {"name": "game minecraft player", "description": "Minecraftのプレイヤーの情報を取得するよ"},
            {"name": "game minecraft java-server", "description": "Javaのサーバーを取得します。"},
            {"name": "game minecraft seedmap", "description": "シード値から構造物などを検索します。"}
        ],
        "ミニゲーム": [
            {"name": "game 8ball", "description": "占ってもらいます。"},
            {"name": "game roll", "description": "さいころを回します。"},
            {"name": "game omikuji", "description": "おみくじを引きます。"},
            {"name": "game lovecalc", "description": "恋愛度計算機で遊びます。"},
            {"name": "game geo-quiz", "description": "地理クイズをで遊びます。"},
            {"name": "game math-quiz", "description": "計算クイズで遊びます。"},
            {"name": "game guess", "description": "数字あてゲームをします。"},
            {"name": "game shiritori", "description": "しりとりをします。"},
            {"name": "game bot-quest", "description": "Botのクエストに挑戦します。"},
            {"name": "fun janken", "description": "じゃんけんをします。"},
        ],
        "誕生日設定": [
            {"name": "fun birthday set", "description": "誕生日を設定します。"},
            {"name": "fun birthday get", "description": "ほかの人の誕生日を取得します。"},
            {"name": "fun birthday list", "description": "今月が誕生日の人を表示します。"}
        ],
        "発言": [
            {"name": "fun say cow", "description": "牛に発言させます。"},
            {"name": "fun say dragon", "description": "ドラゴンに発言させます。"},
            {"name": "fun say pengin", "description": "ペンギンに発言させます。"}
        ],
        "音声・読み上げ": {
            "音声生成・加工": [
                {"name": "fun audio tts", "description": "テキストを音声にします。"},
                {"name": "fun audio distortion", "description": "音割れさせます。"}
            ],
            "読み上げ": [
                {"name": "tts dict add", "description": "読み上げ辞書を追加します。"},
                {"name": "tts dict remove", "description": "読み上げ辞書を削除します。"},
                {"name": "tts dict list", "description": "読み上げ辞書をリスト化します。"},
                {"name": "tts start", "description": "読み上げを開始します。"},
                {"name": "tts end", "description": "読み上げを終了します。"},
                {"name": "tts voice", "description": "読み上げの声を変更します。"},
                {"name": "tts info", "description": "読み上げしているサーバー数を取得します。"},
                {"name": "tts autojoin", "description": "自動接続を設定します。"}
            ],
            "音楽再生": [
                {"name": "music play", "description": "音楽を再生します。"},
                {"name": "music skip", "description": "音楽をスキップします。"},
                {"name": "music stop", "description": "音楽をストップします。"},
                {"name": "music queue", "description": "現在のキューを取得します。"},
                {"name": "music boost", "description": "低温ブーストを設定します。"},
                {"name": "music volume", "description": "ボリュームを設定します。"},
                {"name": "music source", "description": "対応ソースを表示します"}
            ]
        },
        "動画作成": [
            {"name": "fun movie sea", "description": "海の背景の動画に画像を組み合わせます。"}
        ],
        "テキスト・画像作成": {
            "テキスト": [
                {"name": "fun text suddendeath", "description": "突然の死を作成します。"},
                {"name": "fun text retranslate", "description": "再翻訳します。"},
                {"name": "fun text text-to-emoji", "description": "テキストを絵文字にします。"},
                {"name": "fun text reencode", "description": "文字化けさせます。"},
                {"name": "fun text crypt", "description": "文字列を暗号化します。"},
                {"name": "fun text number", "description": "数字の進数を変更します。"},
                {"name": "fun text unicode", "description": "Unicodeに変換します。"},
                {"name": "fun text arm", "description": "armのasmを、バイナリに変換します。"},
                {"name": "fun text morse", "description": "モールス信号に変換します。"}
            ],
            "脳内メーカー":[
                {"name": "fun nounai nounai", "description": "脳内メーカーを使用します。"},
                {"name": "fun nounai kakeizu", "description": "家系図を作成します。"},
                {"name": "fun nounai busyo", "description": "武将メーカーを使用します。"},
                {"name": "fun nounai kabuto", "description": "兜を作成します。"},
                {"name": "fun nounai tenshoku", "description": "転職メーカーを使用します。"}
            ],
            "動物画像": [
                {"name": "fun animal cat", "description": "猫の画像を作成します。"},
                {"name": "fun animal dog", "description": "犬の画像を作成します。"},
                {"name": "fun animal fox", "description": "きつねの画像を作成します。"},
                {"name": "fun animal duck", "description": "アヒルの画像を作成します。"}
            ],
            "画像作成": [
                {"name": "fun image 5000", "description": "5000兆円ほしい！"},
                {"name": "fun image emoji-kitchen", "description": "絵文字キッチンを使用します。"},
                {"name": "fun image textmoji", "description": "テキストを文字にします。"},
                {"name": "fun image httpcat", "description": "HTTPCatを使用します。"},
                {"name": "fun image miq", "description": "Make it a quoteを作成します。"},
                {"name": "fun image ascii", "description": "アスキーアートを作成します。"},
                {"name": "fun image imgur", "description": "Imgurで検索します。"},
                {"name": "fun image game", "description": "ゲームのコラ画像を作成します。"},
                {"name": "fun image profile", "description": "プロフィールを作成します。"}
            ],
            "キャラクター・ランキング": {
                "キャラクター": [
                    {"name": "fun hiroyuki", "description": "ひろゆきを召喚します。"}
                ],
                "ランキング": [
                    {"name": "fun ranking", "description": "ランキングを取得します。"}
                ]
            }
        },
        "サーバー内経済": {
            "基本": [
                {"name": "economy work", "description": "働いて給料を得ます。"},
                {"name": "economy beg", "description": "物乞いをします。"},
                {"name": "economy crime", "description": "犯罪をしてお金を得ます。(リスクあり)"},
                {"name": "economy balance", "description": "サーバー内で残高を取得します。"},
                {"name": "economy pay", "description": "指定したメンバーにサーバー内通貨を送金します。"},
                {"name": "economy deposit", "description": "銀行にお金を預けます。"},
                {"name": "economy withdraw", "description": "銀行からお金を引き出します。"},
                {"name": "economy ranking", "description": "ランキングを取得します。"},
                {"name": "economy buy", "description": "アイテムを買います。"},
                {"name": "economy use", "description": "アイテムを使用します。"},
                {"name": "economy items", "description": "アイテム一覧を取得します。"},
                {"name": "economy game coinflip", "description": "コインの表裏を予想します。"},
                {"name": "economy game blackjack", "description": "ブラックジャックをします。"},
                {"name": "economy game info", "description": "ゲームの情報を取得します。"},
            ],
            "ガチャ": [
                {"name": "economy gacha create", "description": "ガチャを作成します。"},
                {"name": "economy gacha import", "description": "Jsonからガチャをインポートします。"},
                {"name": "economy gacha export", "description": "Jsonにガチャをエクスポートします。"},
                {"name": "economy gacha add", "description": "ガチャにアイテムを追加します。"},
                {"name": "economy gacha multi-add", "description": "確率操作をするために、一つのアイテムを複数追加します。"},
                {"name": "economy gacha remove", "description": "ガチャのアイテムを削除します。"},
                {"name": "economy gacha clear", "description": "ガチャのアイテムをリセットします。"},
                {"name": "economy gacha items", "description": "ガチャから出るアイテムを確認します。"},
                {"name": "economy gacha list", "description": "ガチャリストを確認します。"},
                {"name": "economy gacha buy", "description": "ガチャを引きます。"},
            ],
            "管理": [
                {"name": "economy manage add", "description": "お金を追加します。"},
                {"name": "economy manage remove", "description": "お金を剝奪します。"},
                {"name": "economy manage currency", "description": "新しい通貨名を設定します。"},
                {"name": "economy manage chatmoney", "description": "会話するたびにお金がもらえるようにします。"},
                {"name": "economy item create", "description": "アイテムを作成します。"},
                {"name": "economy item remove", "description": "アイテムを削除します。"},
                {"name": "economy shop item", "description": "アイテムショップパネルを作成します。"}
            ]
        }
    }
}

class CategoryView(discord.ui.View):
    def __init__(self, tree: dict, path: list):
        super().__init__(timeout=180)
        self.add_item(CategorySelect(tree, path))

        if len(path) > 1:
            self.add_item(BackButton(path))

class BackButton(discord.ui.Button):
    def __init__(self, path: list):
        super().__init__(label="← 戻る", style=discord.ButtonStyle.secondary)
        self.path = path

    async def callback(self, interaction: discord.Interaction):
        if len(self.path) <= 1:
            return

        tree = HELP_TREE
        for p in self.path[1:-1]:
            tree = tree[p]

        new_path = self.path[:-1]

        await interaction.response.edit_message(
            content=f"**{' > '.join(new_path)}** に戻りました",
            view=CategoryView(tree, new_path),
            embed=None
        )

class BackOnlyView(discord.ui.View):
    def __init__(self, path: list):
        super().__init__(timeout=180)
        self.add_item(BackButton(path))

class CategorySelect(discord.ui.Select):
    def __init__(self, tree: dict, path: list):
        """
        tree: 今の階層（dict または list）
        path: 現在の階層 ["親", "子", ...]
        """

        self.tree = tree
        self.path = path

        options = [
            discord.SelectOption(label=str(key))
            for key in tree.keys()
        ]

        super().__init__(
            placeholder=" > ".join(path) + " のカテゴリを選択",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]

        next_tree = self.tree[selected]
        new_path = self.path + [selected]

        if isinstance(next_tree, dict):
            await interaction.response.edit_message(
                content=f"**{' > '.join(new_path)} を選択中...**",
                view=CategoryView(next_tree, new_path),
                embed=None
            )
        else:
            embed = make_embed.success_embed(
                title="ヘルプ : " + " > ".join(new_path)
            )

            for cmd in next_tree:
                embed.add_field(
                    name=f"/{cmd['name']}",
                    value=cmd["description"],
                    inline=False
                )

            await interaction.response.edit_message(embed=embed, view=BackOnlyView(self.path), content="")

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> HelpCog")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            a = None
            return a
        elif isinstance(error, commands.CommandOnCooldown):
            a = None
            return a

    @app_commands.command(name="help", description="ヘルプを表示します")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        ヘルプの表示形態=[
            app_commands.Choice(name="見やすくなったヘルプ", value="new"),
            app_commands.Choice(name="カテゴリ別のヘルプ", value="category"),
        ]
    )
    async def help(self, interaction: discord.Interaction, ヘルプの表示形態: app_commands.Choice[str] = None):
        await interaction.response.defer()

        if ヘルプの表示形態 == app_commands.Choice(name="見やすくなったヘルプ", value="new"):
            embeds = []

            commands_list = list(self.bot.tree.get_commands())

            def new_embed():
                return make_embed.success_embed(
                    title="SharkBotのヘルプ (スラッシュコマンド版)",
                    description="スラッシュコマンド版のヘルプです。\n頭文字コマンド用ヘルプは `!.help` を使用してください。"
                )

            embed = new_embed()
            field_count = 0

            for c in commands_list:
                if isinstance(c, app_commands.Command):
                    name = f"/{c.name}"
                    desc = c.description or "説明なし"
                    embed.add_field(name=name, value=desc, inline=False)
                    field_count += 1

                elif isinstance(c, app_commands.Group):
                    for cc in c.commands:
                        name = f"/{c.name} {cc.name}"
                        desc = cc.description or "説明なし"
                        embed.add_field(name=name, value=desc, inline=False)
                        field_count += 1

                        if field_count >= 10:
                            embeds.append(embed)
                            embed = new_embed()
                            field_count = 0

                if field_count >= 10:
                    embeds.append(embed)
                    embed = new_embed()
                    field_count = 0

            if field_count > 0:
                embeds.append(embed)

            class Help_view(discord.ui.View):
                def __init__(self, get_commands):
                    super().__init__()
                    self.get_commands = get_commands
                    self.current_page = 0
                    self.update_buttons()

                def update_buttons(self):
                    self.clear_items()
                    self.add_item(
                        discord.ui.Button(
                            emoji="⏮️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_prex_skip_beta",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="◀️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_prev_beta",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            label=f"{self.current_page + 1}/{len(embeds)}",
                            style=discord.ButtonStyle.secondary,
                            disabled=True,
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="▶️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_next_beta",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="⏭️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_next_skip_beta",
                        )
                    )

                async def interaction_check(self, interaction: discord.Interaction) -> bool:
                    try:
                        if interaction.data["custom_id"] == "help_prev_beta":
                            if self.current_page > 0:
                                self.current_page -= 1
                        elif interaction.data["custom_id"] == "help_next_beta":
                            if self.current_page < len(embeds) - 1:
                                self.current_page += 1
                            else:
                                self.current_page = 0
                        elif interaction.data["custom_id"] == "help_next_skip_beta":
                            self.current_page = len(embeds) - 1
                        elif interaction.data["custom_id"] == "help_prex_skip_beta":
                            self.current_page = 0
                        self.update_buttons()
                        await interaction.response.edit_message(
                            embed=embeds[self.current_page], view=self
                        )
                        return True
                    except:
                        return True

            view = Help_view(self.get_commands)
            await interaction.followup.send(embed=embeds[0], view=view)
            return
        elif ヘルプの表示形態 == app_commands.Choice(name="カテゴリ別のヘルプ", value="category"):
            pages = []

            pages.append(discord.Embed(title="カテゴリ別のヘルプ", description="▶️ ボタンでメインのヘルプを閲覧できます。", color=discord.Color.blue()).add_field(name="このヘルプについて", value="スラッシュコマンド版のヘルプです。\n頭文字コマンド用ヘルプは !.help を使用してください。", inline=False))

            for c in self.bot.tree.get_commands():
                if type(c) == app_commands.Command:
                    pages.append(
                        discord.Embed(
                            title=f"/{c.name}",
                            description=f"{c.description}",
                            color=discord.Color.blue(),
                        )
                    )
                elif type(c) == app_commands.Group:
                    embed = discord.Embed(title=f"/{c.name} ({c.description})", color=discord.Color.blue())
                    text = ""
                    for cc in c.commands:
                        text += f"{cc.name} .. {cc.description}\n"
                    embed.description = text
                    pages.append(embed)

            class Help_view(discord.ui.View):
                def __init__(self, get_commands):
                    super().__init__()
                    self.get_commands = get_commands
                    self.current_page = 0
                    self.update_buttons()

                def update_buttons(self):
                    self.clear_items()
                    self.add_item(
                        discord.ui.Button(
                            emoji="⏮️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_prex_skip",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="◀️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_prev",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            label=f"{self.current_page + 1}/{len(pages)}",
                            style=discord.ButtonStyle.secondary,
                            disabled=True,
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="▶️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_next",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="⏭️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_next_skip",
                        )
                    )

                async def interaction_check(self, interaction: discord.Interaction) -> bool:
                    try:
                        if interaction.data["custom_id"] == "help_prev":
                            if self.current_page > 0:
                                self.current_page -= 1
                        elif interaction.data["custom_id"] == "help_next":
                            if self.current_page < len(pages) - 1:
                                self.current_page += 1
                            else:
                                self.current_page = 0
                        elif interaction.data["custom_id"] == "help_next_skip":
                            self.current_page = len(pages) - 1
                        elif interaction.data["custom_id"] == "help_prex_skip":
                            self.current_page = 0
                        self.update_buttons()
                        await interaction.response.edit_message(
                            embed=pages[self.current_page], view=self
                        )
                        return True
                    except:
                        return True

            view = Help_view(self.get_commands)
            await interaction.followup.send(embed=pages[0], view=view)
            return

        await interaction.followup.send(
            content="**カテゴリを選択してください**",
            view=CategoryView(HELP_TREE, ["ヘルプ"])
        )
        await interaction.followup.send(ephemeral=True, content="従来のヘルプを表示するには、\n/helpでカテゴリ別のヘルプを選択してください。")

    @app_commands.command(
        name="dashboard", description="ダッシュボードのリンクを取得します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def dashboard(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.send_message(
            f"現在はダッシュボードにアクセスできません。",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
