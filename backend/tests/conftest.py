"""Test setup: import the backend, use an in-memory MongoDB and a throwaway risk model file."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["MONGO_URI"] = "mongomock://"
os.environ["RISK_MODEL_PATH"] = os.path.join(tempfile.mkdtemp(), "risk.joblib")
