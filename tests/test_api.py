import unittest
from fastapi.testclient import TestClient
from slot_engine.api.app import app

class TestSlotAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        res = self.client.get("/api/slot/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ONLINE")
        self.assertEqual(data["game"], "The Descent: Abyssal Leviathan")
        self.assertIn("96.05%", data["rtp"])

    def test_paytable_endpoint(self):
        res = self.client.get("/api/slot/paytable")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("paytable", data)
        self.assertIn("pressure_points", data)
        self.assertIn("feature_buys", data)

    def test_spin_endpoint(self):
        res = self.client.post("/api/slot/spin", json={"bet": 1.0, "feature_buy": "NONE"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("spin_id", data)
        self.assertIn("events", data)
        self.assertGreaterEqual(data["total_payout"], 0.0)

    def test_bonus_buy_standard(self):
        res = self.client.post("/api/slot/buy-bonus", json={"bet": 1.0, "feature_type": "STANDARD_BONUS_100X"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["bet"], 100.0)
        self.assertGreater(len(data["events"]), 0)

    def test_bonus_buy_ultra(self):
        res = self.client.post("/api/slot/buy-bonus", json={"bet": 1.0, "feature_type": "ULTRA_BONUS_350X"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["bet"], 350.0)
        self.assertGreater(len(data["events"]), 0)

    def test_root_serves_html(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("The Descent: Abyssal Leviathan", res.text)


if __name__ == "__main__":
    unittest.main()
