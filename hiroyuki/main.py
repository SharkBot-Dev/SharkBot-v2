from sentence_transformers import SentenceTransformer, util
from flask import Flask, request

model = SentenceTransformer("all-MiniLM-L6-v2")

candidates = [
    "それで勝った気になってるんですか？だったら相当頭悪いっすね",
    "なんかそういうのって頭悪いか、嘘つきかのどちらかですよ",
    "それってほぼ詐欺ですよね",
    "それって明らかではないですよね？",
    "頭の悪い人は目立つんですよ",
    "それって答えになってないですよね？",
    "それはそう言う風にしか理解できない知能の問題だと思いますけどね",
    "不快感を覚えた自分に驚いたんだよね",
    "それっておかしくないですか？",
    "僕の方が詳しいと思うんすよ",
    "それってあなたの感想ですよね？",
    "あなた相当頭悪いですよね…",
    "それってあなたの想像ですよね？",
    "なんか言いました？",
    "「欲しいものを手に入れたい」という欲望って、埋まらないんですよ",
    "社会ってそんなもんじゃないんですか？",
    "それって矛盾してますよね？",
    "ちょっと日本語わかりづらいんですけどどちらの国の方ですか？",
    "データなんかねえよ",
    "根拠なしに話すのやめてもらえますか？",
    "さっきと言ってること違いません？",
    "「すいません」？なんすか「すいません」って...",
    "何だろう。すみませんって言ってもらってもいいですか？",
    "それで勝った気になってるんですか？だったら相当頭悪いっすね",
]


app = Flask(__name__)


@app.get("/")
def hiroyuki():
    target_vec = model.encode(request.args.get("text", "こんにちは"))
    candidate_vecs = model.encode(candidates)

    similarities = [util.cos_sim(target_vec, c_vec).item() for c_vec in candidate_vecs]
    best_index = similarities.index(max(similarities))
    return candidates[best_index]


app.run(port=6100, host="0.0.0.0", debug=False)
