from flask import Flask, request, send_file, jsonify
import matplotlib.pyplot as plt
import matplotlib
import io

matplotlib.use("Agg")

app = Flask(__name__)


@app.route("/piechart", methods=["POST"])
def create_pie_chart():
    data = request.json

    if not data or "labels" not in data or "values" not in data or "title" not in data:
        return jsonify({"error": "Missing labels or values or Title"}), 400

    labels = data["labels"]
    values = data["values"]
    title = data["title"]

    if len(labels) != len(values):
        return jsonify({"error": "labels and values must have the same length"}), 400

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")

    plt.title(title)

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype="image/png")


@app.route("/plot", methods=["POST"])
def create_plot():
    data = request.json

    if (
        not data
        or "xvalues" not in data
        or "yvalues" not in data
        or "title" not in data
    ):
        return jsonify({"error": "Invalid input"}), 400

    x_values = data["xvalues"]
    y_values = data["yvalues"]
    title = data["title"]

    try:
        y_values = [int(v) for v in y_values]
    except ValueError:
        return jsonify({"error": "yvalues must be numeric"}), 400

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x_values, y_values, marker="o")

    plt.xticks(rotation=45, ha="right")
    plt.title(title)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True, port=3067, host="0.0.0.0")
