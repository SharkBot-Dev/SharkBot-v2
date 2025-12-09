import signal
from flask import Flask, request, send_file, jsonify
import matplotlib.pyplot as plt
import matplotlib
import sympy as sp
import numpy as np
import io

matplotlib.use("Agg")

app = Flask(__name__)

class TimeoutError(Exception):
    pass

def handler(signum, frame):
    raise TimeoutError("計算がタイムアウトしました")

def evaluate_formula_with_timeout(expr, X, timeout_sec=1):
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_sec)

    try:
        f = sp.lambdify(sp.symbols("x"), expr, modules=["numpy"])
        Y = f(X)
    finally:
        signal.alarm(0)

    return Y


@app.route("/formula", methods=["POST"])
def formula_plot():
    try:
        body = request.get_json()

        formula = body.get("formula")
        xmin = body.get("xmin", -10)
        xmax = body.get("xmax", 10)

        x = sp.symbols("x")
        try:
            expr = sp.sympify(formula)
        except Exception:
            return jsonify({"error": "invalid formula"}), 400

        X = np.linspace(xmin, xmax, 500)

        try:
            Y = evaluate_formula_with_timeout(expr, X, timeout_sec=1)
        except TimeoutError:
            return jsonify({"error": "formula timeout"}), 408
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"error": "Error."}), 500

        buf = io.BytesIO()
        plt.figure(figsize=(6, 4))
        plt.plot(X, Y)
        plt.title(f"y = {formula}")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)

        return send_file(buf, mimetype="image/png")

    except Exception as e:
        return jsonify({"error": f"{e}"}), 500
    
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

# app.run("0.0.0.0", port=3067)