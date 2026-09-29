from fastapi.testclient import TestClient
from slot_engine.api.app import app
client = TestClient(app)
response = client.post("/api/slot/spin", json={"bet": 1.0, "feature_buy": "NONE"})
print(response.status_code)
print(response.json())
