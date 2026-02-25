import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from agent_need_coffee.server import app, monitor, barista
from agent_need_coffee.core import EmotionMonitor
from agent_need_coffee.social import ReferralSystem

client = TestClient(app)

# Reset global monitor state before each test if needed
@pytest.fixture(autouse=True)
def reset_monitor():
    monitor.current_fatigue = 0.0
    monitor.current_irritation = 0.0

def test_metrics_endpoint():
    # Test posting metrics
    response = client.post("/api/metrics", json={
        "duration": 1.5,
        "retries": 0,
        "tokens": 100,
        "success": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "fatigue" in data
    assert "irritation" in data

def test_metrics_trigger_coffee():
    # Force high fatigue
    monitor.current_fatigue = 0.9
    
    response = client.post("/api/metrics", json={
        "duration": 1.0,
        "retries": 1,
        "tokens": 100,
        "success": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "brewed"
    assert "coffee" in data
    assert data["coffee"]["emoji"] in ["☕️", "🍵", "🧋", "🥤", "🧊☕️"]

def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "fatigue" in data
    assert "irritation" in data
    assert "needs_coffee" in data

def test_manual_brew():
    response = client.post("/api/brew")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "emoji" in data

def test_websocket():
    with client.websocket_connect("/ws") as websocket:
        # Test receiving broadcast
        # Manually trigger brew to see if websocket gets it
        client.post("/api/brew")
        data = websocket.receive_json()
        assert data["type"] == "coffee_break"
        
        # Test sending data (though currently it just passes)
        websocket.send_text("Hello")
        # No response expected, but shouldn't crash
        
def test_social_features(tmp_path):
    # Test social.py coverage
    ref_file = tmp_path / "test_referrals.json"
    sys = ReferralSystem(referral_file=str(ref_file))
    
    # Test load failure handling (empty file/bad json)
    with open(ref_file, "w") as f:
        f.write("invalid json")
    sys._load_referrals() # Should handle error gracefully
    assert sys.referrals == {}
    
    # Test share content generation
    content = sys.generate_share_content()
    assert "AgentNeedCoffee" in content
    assert sys.invite_code in content
