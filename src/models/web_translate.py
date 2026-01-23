import aiohttp
import urllib.parse

def targetToSource(target: str):
    return {
        "ja": "en",
        "en": "ja",
        "zh-CN": "ja",
        "ko": "ja",
        "ru": "ja"
    }.get(target, "en")

async def translate(source: str, target: str, text: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://translate.googleapis.com/translate_a/single?client=gtx&sl={source}&tl={target}&dt=t&dj=1&q={urllib.parse.quote(text)}') as response:
            data = await response.json()

            translated_text = "".join(sentence['trans'] for sentence in data.get('sentences', []))
            source_language = data.get('src', source)

            return {
                "text": translated_text,
                "source": source_language
            }