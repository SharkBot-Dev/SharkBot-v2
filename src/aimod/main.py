from transformers import pipeline
from flask import Flask, request

classifier = pipeline(
    "text-classification",
    model="ptaszynski/yacis-electra-small-japanese-cyberbullying",
    tokenizer="ptaszynski/yacis-electra-small-japanese-cyberbullying",
)

app = Flask(__name__)


@app.post("/")
def index():
    result = classifier(request.json.get("text", "こんにちは"))
    return result


app.run(port=6200, host="0.0.0.0", debug=False)
