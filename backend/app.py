"""AgriCred API: alternative credit evaluation for smallholder farmers.

Run:  python app.py   (http://localhost:5000)
"""
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from agricred import crops, db, risk_model
from agricred.assessment import ValidationError, assess

app = Flask(__name__)
CORS(app)


def error(message, status=400):
    return jsonify({"error": message}), status


@app.get("/api/health")
def health():
    ok, message = db.ping()
    return jsonify({"ok": ok, "message": message})


@app.get("/api/crops")
def crop_catalogue():
    return jsonify({
        "crops": [{"name": n, "season": c["season"], "msp": c["msp"], "yield_per_acre": c["yield_"]}
                  for n, c in crops.CROPS.items()],
        "soils": crops.SOILS, "source": crops.PRICE_SOURCE,
    })


@app.post("/api/assessments")
def create():
    try:
        result = assess(request.get_json(silent=True) or {})
    except ValidationError as e:
        return error(str(e))
    if request.args.get("save", "1") == "0":
        return jsonify(result)
    try:
        return jsonify(db.save(result)), 201
    except Exception:
        return error("Could not save to MongoDB. Is the MongoDB service running?", 503)


@app.get("/api/assessments")
def list_():
    try:
        return jsonify(db.search(request.args.get("q", "").strip()[:60]))
    except Exception:
        return error("Could not read from MongoDB. Is the MongoDB service running?", 503)


@app.get("/api/assessments/<id_>")
def get_one(id_):
    doc = db.get(id_)
    return jsonify(doc) if doc else error("Assessment not found", 404)


@app.delete("/api/assessments/<id_>")
def delete(id_):
    return ("", 204) if db.delete(id_) else error("Assessment not found", 404)


@app.get("/api/stats")
def stats():
    try:
        s = db.stats()
    except Exception:
        return error("Could not read from MongoDB. Is the MongoDB service running?", 503)
    s["model_auc"] = risk_model.load()["auc"]
    return jsonify(s)


if __name__ == "__main__":
    risk_model.load()  # trains the model on first run
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
