questions, characters = (
    [
        {"id": "anime", "text": "そのキャラはアニメのキャラですか？"},
        {"id": "human", "text": "そのキャラは人間ですか？"},
        {"id": "blue_hair", "text": "そのキャラは青髪ですか？"},
        {"id": "japan", "text": "そのキャラは日本人ですか？"},
        {"id": "discord", "text": "その人はdiscordをやっていますか？"},
    ],
    {
        "レム": {"anime": True, "human": False, "blue_hair": True, "japan": False},
        "ナルト": {
            "anime": True,
            "human": True,
            "blue_hair": False,
        },
        "イチロー": {"anime": False, "human": True, "blue_hair": False, "japan": True},
        "ろゆまな（？）": {
            "human": True,
            "japan": True,
            "discord": True,
            "anime": False,
            "blue_hair": False,
        },
    },
)
