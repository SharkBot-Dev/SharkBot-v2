import asyncio
import random
from janome.tokenizer import Tokenizer
from functools import partial

HIROYUKI_TEXT = """
それってあなたの感想ですよね？
なんかそういうのって頭悪いか、嘘つきかのどちらかですよ。
それで勝った気になってるんですか？だったら相当頭悪いっすね。
それってほぼ詐欺ですよね。
ダメだこりゃ（笑）。
なんだろう、まだ始まってもないのに諦めるのやめてもらっていいですか？
はい論破
それって明らかではなくて、あなたの感想ですよね？
本当つまんないっすよ
それが偉いんですか？
僕の方が詳しいと思うんすよ
それっておかしくないですか？
ちょっと日本語わかりづらいんですけどどちらの国の方ですか？
Bot相手にイラついて恥ずかしくないの？w
頭の悪い人は目立つんですよ
嘘は嘘であると見抜ける人でないと(SharkBOTを使うのは)難しい
"""

async def generate_text(text: str, started_word: str, max_words: int = 50):
    loop = asyncio.get_running_loop()
    tokenizer = await loop.run_in_executor(None, Tokenizer)

    words = [token.surface for token in await loop.run_in_executor(None, partial(tokenizer.tokenize, text))]

    markov = {}
    for i in range(len(words) - 2):
        key = (words[i], words[i + 1])
        next_word = words[i + 2]
        markov.setdefault(key, []).append(next_word)

    def generate_sentence(start_word=None, max_words=50):
        if start_word:
            candidates = [k for k in markov.keys() if start_word in k]
            start = random.choice(candidates) if candidates else random.choice(list(markov.keys()))
        else:
            start = random.choice(list(markov.keys()))

        sentence = [start[0], start[1]]
        for _ in range(max_words):
            key = tuple(sentence[-2:])
            if key in markov:
                next_word = random.choice(markov[key])
                sentence.append(next_word)
                if next_word in ("。", "！", "？"):
                    break
            else:
                break
        return "".join(sentence)

    gen_text = await loop.run_in_executor(None, partial(generate_sentence, started_word, max_words))
    return started_word + gen_text