"""MongoDB storage for assessments.

Set MONGO_URI to point at your server (default: local MongoDB on port 27017).
MONGO_URI=mongomock:// uses an in-memory fake database, for tests and demos.
"""
import os

from bson import ObjectId
from pymongo import DESCENDING

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "agricred")

_client = None


def client():
    global _client
    if _client is None:
        if MONGO_URI.startswith("mongomock://"):
            import mongomock
            _client = mongomock.MongoClient()
        else:
            from pymongo import MongoClient
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client


def assessments():
    col = client()[DB_NAME]["assessments"]
    return col


def ping():
    try:
        client().admin.command("ping")
        return True, "Connected to MongoDB"
    except Exception as e:  # pragma: no cover - depends on the local server
        return False, f"Cannot reach MongoDB at {MONGO_URI}. Is the MongoDB service running? ({e.__class__.__name__})"


def _out(doc):
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


def save(doc):
    res = assessments().insert_one(dict(doc))
    return _out({**doc, "_id": res.inserted_id})


def get(id_):
    try:
        return _out(assessments().find_one({"_id": ObjectId(id_)}))
    except Exception:
        return None


def delete(id_):
    try:
        return assessments().delete_one({"_id": ObjectId(id_)}).deleted_count > 0
    except Exception:
        return False


def search(q="", limit=100):
    query = {}
    if q:
        rx = {"$regex": q, "$options": "i"}
        query = {"$or": [{"farmer.name": rx}, {"farmer.village": rx}, {"farmer.district": rx}]}
    fields = {"farmer": 1, "score": 1, "band": 1, "decision": 1, "decision_label": 1,
              "suggested_limit": 1, "requested_amount": 1, "created_at": 1, "risk.probability_of_default": 1,
              "inputs.current_crop": 1}
    return [_out(d) for d in assessments().find(query, fields).sort("created_at", DESCENDING).limit(limit)]


def stats():
    docs = list(assessments().find({}, {"band": 1, "decision": 1, "suggested_limit": 1, "score": 1}))
    n = len(docs)
    bands = {b: 0 for b in "ABCDE"}
    decisions = {d: 0 for d in ("approve", "conditional", "review", "decline")}
    for d in docs:
        bands[d["band"]] += 1
        decisions[d["decision"]] += 1
    return {
        "total": n,
        "average_score": round(sum(d["score"] for d in docs) / n, 1) if n else None,
        "approval_rate": round((decisions["approve"] + decisions["conditional"]) / n, 3) if n else None,
        "total_suggested_credit": sum(d["suggested_limit"] for d in docs),
        "bands": bands, "decisions": decisions,
    }
